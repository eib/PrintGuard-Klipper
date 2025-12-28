"""Utility for syncing settings between printer config and stream processor."""

import logging
from .streams import stream_manager

logger = logging.getLogger(__name__)


def sync_stream_settings(
    printer_id: str,
    sensitivity: float,
    majority_voting: int,
    target_fps: float,
    detection_action: str
):
    """Sync printer settings to active stream processor.
    
    Args:
        printer_id: ID of the printer
        sensitivity: Inference sensitivity
        majority_voting: Majority voting window
        target_fps: Target frames per second
        detection_action: Detection action (none/pause/stop)
    """
    source = stream_manager.get_source(printer_id)
    if not source:
        return
        
    logger.info(
        f"Syncing settings for {printer_id}: "
        f"sensitivity={sensitivity}, target_fps={target_fps}"
    )
    
    source.settings.sensitivity = sensitivity
    source.settings.majority_voting = majority_voting
    source.settings.target_fps = target_fps
    source.settings.detection_action = detection_action
    source.processor.settings = source.settings

