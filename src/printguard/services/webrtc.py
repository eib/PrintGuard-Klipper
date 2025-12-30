"""WebRTC video processing - inference only, delegates side effects."""

import asyncio
import logging
import time
from collections import deque, Counter
from datetime import datetime
from io import BytesIO
from typing import Callable, Optional

from aiortc import RTCDataChannel, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame
from PIL import ImageEnhance

from .storage import screenshot_manager
from .events import event_service
from ..core.models import FeedSettings, PredictionResult, PredictionStatus, PredictionClass

logger = logging.getLogger(__name__)

relay = MediaRelay()
pcs: set[RTCPeerConnection] = set()


class VideoProcessor:
    """Process video frames and run inference. Emits events via callbacks."""

    def __init__(self, predict_fn: Callable, model_info: dict, settings: FeedSettings, session_id: Optional[str] = None):
        self.predict_fn = predict_fn
        self.model_info = model_info
        self.settings = settings
        self.session_id = session_id
        self.printer_id: Optional[str] = None
        self.last_result: dict | None = None
        self.data_channels: set[RTCDataChannel] = set()
        self.relayed_track = None
        self._latest_frame: VideoFrame | None = None
        self._frame_ready = asyncio.Event()
        self._running = True
        self.pause_inference = getattr(settings, "inference_paused", False)
        self._results_buffer = deque(maxlen=50)
        self._timeline_buffer = deque(maxlen=200)
        self._inference_times = deque(maxlen=10)
        self._last_inference_time = 0
        self._defect_handled = False
        self.on_defect: Optional[Callable[[str, float, Optional[str]], None]] = None

    def add_data_channel(self, channel: RTCDataChannel):
        """Add a data channel for result streaming."""
        self.data_channels.add(channel)

        @channel.on("statechange")
        def on_statechange():
            if channel.readyState == "closed":
                self.data_channels.discard(channel)

    async def _receive_frames(self, track):
        """Receive frames, keeping only the latest."""
        while self._running:
            try:
                frame: VideoFrame = await track.recv()
                self._latest_frame = frame
                self._frame_ready.set()
            except MediaStreamError:
                self._running = False
                self._frame_ready.set()
                break
            except Exception as e:
                logger.error(f"Frame receive error: {e}")
                self._running = False
                self._frame_ready.set()
                break

    async def _run_inference(self):
        """Main inference loop."""
        while self._running:
            if self.pause_inference:
                self._defect_handled = False
                await asyncio.sleep(0.1)
                continue

            if 0 < self.settings.target_fps < 100:
                elapsed = time.time() - self._last_inference_time
                wait_time = (1.0 / self.settings.target_fps) - elapsed
                if wait_time > 0.001:
                    await asyncio.sleep(wait_time)

            await self._frame_ready.wait()
            if not self._running:
                break

            frame = self._latest_frame
            self._frame_ready.clear()
            if frame is None:
                continue

            self._last_inference_time = time.time()
            self._inference_times.append(self._last_inference_time)

            # Preprocess image
            image = frame.to_image()
            if self.settings.resolution:
                image = image.resize(self.settings.resolution)
            if self.settings.brightness != 1.0:
                image = ImageEnhance.Brightness(image).enhance(self.settings.brightness)
            if self.settings.contrast != 1.0:
                image = ImageEnhance.Contrast(image).enhance(self.settings.contrast)

            # Run inference
            result = await asyncio.to_thread(
                self.predict_fn, image, self.model_info, self.settings.sensitivity
            )

            if not result:
                continue

            # Store for timeline
            self._results_buffer.append(result.get("class_name"))
            probs = result.get("probabilities", {})
            defect_conf = probs.get("defect", 0.0)
            if not defect_conf and "defect_idx" in self.model_info:
                idx = self.model_info["defect_idx"]
                class_names = self.model_info.get("class_names", [])
                if 0 <= idx < len(class_names):
                    defect_conf = probs.get(class_names[idx], 0.0)

            self._timeline_buffer.append({
                "timestamp": self._last_inference_time,
                "class_name": result.get("class_name"),
                "confidence": result.get("confidence"),
                "defect_confidence": defect_conf,
                "class_idx": result.get("class_idx")
            })
            latest_timeline_entry = self._timeline_buffer[-1]

            # Calculate actual FPS
            actual_fps = 0.0
            if len(self._inference_times) > 1:
                duration = self._inference_times[-1] - self._inference_times[0]
                if duration > 0:
                    actual_fps = (len(self._inference_times) - 1) / duration

            # Apply majority voting
            window_size = max(1, self.settings.majority_voting)
            recent_results = list(self._results_buffer)[-window_size:]
            if recent_results:
                majority_class = Counter(recent_results).most_common(1)[0][0]
                result["class_name"] = majority_class

            result["actual_fps"] = actual_fps
            self.last_result = result

            # Broadcast via WebSocket
            broadcast_id = self.printer_id or self.session_id
            if broadcast_id:
                await event_service.broadcast(broadcast_id, "inference", {
                    "class_name": result.get("class_name"),
                    "confidence": result.get("confidence"),
                    "actual_fps": actual_fps,
                    "paused": self.pause_inference,
                    "timeline_entry": latest_timeline_entry
                })

            # Send via data channel
            result_model = PredictionResult(**result, status=PredictionStatus.SUCCESS)
            message = result_model.model_dump_json()
            for dc in list(self.data_channels):
                if dc.readyState == "open":
                    try:
                        dc.send(message)
                    except Exception:
                        self.data_channels.discard(dc)

            # Handle defect detection
            class_name = result_model.class_name
            if class_name and class_name != PredictionClass.NORMAL and not self._defect_handled:
                self._defect_handled = True
                screenshot_path = self._save_screenshot(frame)
                if self.on_defect:
                    try:
                        if asyncio.iscoroutinefunction(self.on_defect):
                            asyncio.create_task(self.on_defect(str(class_name), result_model.confidence or 0, screenshot_path))
                        else:
                            self.on_defect(str(class_name), result_model.confidence or 0, screenshot_path)
                    except Exception as e:
                        logger.error(f"Defect callback error: {e}")

    def _save_screenshot(self, frame: VideoFrame) -> Optional[str]:
        """Save frame as screenshot, return filename."""
        try:
            filename = f"defect_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            buf = BytesIO()
            frame.to_image().save(buf, format="JPEG")
            screenshot_manager.add(filename, buf.getvalue())
            return filename
        except Exception as e:
            logger.error(f"Screenshot save failed: {e}")
            return None

    def get_timeline_results(self) -> list[dict]:
        """Get timeline buffer."""
        return list(self._timeline_buffer)

    async def process(self, track):
        """Process video track."""
        receiver_task = asyncio.create_task(self._receive_frames(track))
        inference_task = asyncio.create_task(self._run_inference())
        await asyncio.gather(receiver_task, inference_task)


async def create_peer_connection(
    offer: RTCSessionDescription,
    predict_fn: Callable,
    model_info: dict,
    settings: FeedSettings,
    session_id: Optional[str] = None
) -> tuple[RTCPeerConnection, VideoProcessor]:
    """Create WebRTC peer connection with video processing."""
    pc = RTCPeerConnection()
    pcs.add(pc)
    processor = VideoProcessor(predict_fn, model_info, settings, session_id)

    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ["closed", "failed"]:
            pcs.discard(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        processor.add_data_channel(channel)

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            relayed_track = relay.subscribe(track)
            processor.relayed_track = relayed_track
            asyncio.create_task(processor.process(relayed_track))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc, processor


async def start_track_processing(
    track,
    predict_fn: Callable,
    model_info: dict,
    settings: FeedSettings,
    session_id: Optional[str] = None
) -> VideoProcessor:
    """Start processing a MediaStreamTrack directly."""
    processor = VideoProcessor(predict_fn, model_info, settings, session_id)
    relayed_track = relay.subscribe(track)
    processor.relayed_track = relayed_track
    asyncio.create_task(processor.process(relayed_track))
    return processor


async def create_viewer_connection(
    offer: RTCSessionDescription,
    processor: VideoProcessor
) -> RTCPeerConnection:
    """Create a viewer WebRTC connection for an existing processor."""
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ["closed", "failed"]:
            pcs.discard(pc)

    if processor.relayed_track:
        pc.addTrack(processor.relayed_track)
    dc = pc.createDataChannel("results")
    processor.add_data_channel(dc)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc


async def cleanup():
    """Close all peer connections."""
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
