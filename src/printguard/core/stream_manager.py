import asyncio
import logging
from typing import Optional, List
import cv2
from pydantic import BaseModel

from .db.session import ServiceManager
from .db.types import ComponentType  
from .config import settings
from .connections.base import BaseConnection
from .networking import http_client, RequestParams, HTTPMethod

logger = logging.getLogger(__name__)

class MediaMTXPathConfig(BaseModel):
    source: str
    sourceOnDemand: bool = False

class StreamManager:
    """Manages camera streams via MediaMTX."""
    
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self.base_api_url = settings.MEDIAMTX_API_URL
        self.base_webrtc_url = settings.MEDIAMTX_WEBRTC_URL

    async def register_camera(self, path: str, source_url: str) -> bool:
        """Registers a camera stream with MediaMTX."""
        is_registered = await self.check_health(path)
        if is_registered:
            await self.unregister_camera(path)
        
        response = await http_client.run_async(
            params=RequestParams(
                url=f"{self.base_api_url}/config/paths/add/{path}",
                method=HTTPMethod.POST,
                json_data={
                    "source": source_url,
                    "sourceOnDemand": False
                }
            )
        )
        
        if response.is_success:
            logger.info(f"Registered camera {path} with MediaMTX")
            return True
        else:
            logger.error(f"Failed to register camera {path}: {response.content}")
            return False

    async def unregister_camera(self, path: str) -> bool:
        """Unregisters a camera stream from MediaMTX."""
        response = await http_client.run_async(
            params=RequestParams(
                url=f"{self.base_api_url}/config/paths/delete/{path}",
                method=HTTPMethod.DELETE
            )
        )
        
        if response.is_success or response.status_code == 404:
            logger.info(f"Unregistered camera {path}")
            return True
        else:
            logger.error(f"Failed to unregister camera {path}: {response.content}")
            return False

    async def get_active_paths(self) -> List[str]:
        """Get list of active path names from MediaMTX."""
        response = await http_client.run_async(
            params=RequestParams(
                url=f"{self.base_api_url}/paths/list",
                method=HTTPMethod.GET
            )
        )
        
        if response.is_success:
            items = response.content.get("items", []) if response.content else []
            return [item.get("name") for item in items if item]
        else:
            logger.error(f"Failed to list paths: {response.content}")
            return []

    async def sync_cameras(self):
        """Syncs DB cameras with MediaMTX configuration."""
        logger.info("Syncing cameras with MediaMTX...")
        try:
            db_cameras = await self.service_manager.components.list_full() 
            db_cameras = [c for c in db_cameras if c.type == ComponentType.CAMERA]
        except Exception as e:
            logger.error(f"Failed to fetch cameras from DB: {e}")
            return
        active_paths = set()
        for cam in db_cameras:
            try:
                connection: BaseConnection = self.service_manager.connections.get(cam.connection_id)
                if not connection:
                    logger.warning(f"Connection not found for camera {cam.id}")
                    continue
                stream_url = await connection.get_stream_url(cam)
                if stream_url:
                    path = str(cam.id)
                    success = await self.register_camera(path, stream_url)
                    if success:
                        active_paths.add(path)
                else:
                    logger.warning(f"No stream URL found for camera {cam.id}")
            except Exception as e:
                logger.error(f"Error syncing camera {cam.id}: {e}")
        current_paths = await self.get_active_paths()
        for path in current_paths:
            if path not in active_paths:
                logger.info(f"Removing unknown path: {path}")
                await self.unregister_camera(path)

    async def get_webrtc_url(self, path: str) -> str:
        """Returns the WebRTC URL for the frontend."""
        return f"{self.base_webrtc_url}/{path}"
    
    async def check_health(self, path: str) -> bool:
        """Checks if the stream is online in MediaMTX."""
        response = await http_client.run_async(
            params=RequestParams(
                url=f"{self.base_api_url}/paths/get/{path}",
                method=HTTPMethod.GET
            )
        )
        if response.is_success and response.status_code == 200:
            return response.content.get("ready", False) if response.content else False
        return False

    async def get_snapshot(self, path: str) -> Optional[bytes]:
        """Gets a snapshot from the camera stream."""
        rtsp_url = f"rtsp://localhost:8554/{path}"

        def _capture():
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                return None
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                is_success, buffer = cv2.imencode(".jpg", frame)
                if is_success:
                    return buffer.tobytes()
            return None
        return await asyncio.to_thread(_capture)