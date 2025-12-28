"""Centralized defect handling logic."""

import logging
from sqlalchemy import select

from ..core.database import async_session as SessionLocal
from ..core.db_models import Printer
from .notifications import notify_defect

logger = logging.getLogger(__name__)


async def handle_defect(
    printer_id: str,
    session_id: str,
    class_name: str,
    confidence: float,
    screenshot_path: str = None,
    detection_action: str = "none"
):
    """Handle a detected defect.
    
    Args:
        printer_id: ID of the printer
        session_id: WebRTC session ID
        class_name: Detected defect class
        confidence: Detection confidence
        screenshot_path: Optional path to screenshot
        detection_action: Action to take (none/pause/stop)
    """
    # Trigger printer action if configured
    if detection_action and detection_action != "none":
        await trigger_printer_action(printer_id, detection_action)
    
    # Pause inference in database
    async with SessionLocal() as db:
        res = await db.execute(
            select(Printer).where(Printer.id == printer_id)
        )
        db_printer = res.scalar_one_or_none()
        if db_printer:
            db_printer.inference_paused = True
            await db.commit()
    
    # Send notification
    notify_defect(session_id, class_name, confidence, screenshot_path)


async def trigger_printer_action(printer_id: str, action: str):
    """Trigger an action on a printer.
    
    Args:
        printer_id: ID of the printer
        action: Action to trigger (pause/stop)
    """
    if action == "none":
        return
    
    from ..api.routes.printer import _get_or_create_printer_instance
    
    async with SessionLocal() as db:
        instance = await _get_or_create_printer_instance(printer_id, db)
        if not instance or not instance.control:
            logger.warning(
                f"Cannot trigger {action} for printer {printer_id}: "
                "instance or control not found"
            )
            return
            
        try:
            if action == "pause":
                logger.info(f"Auto-pausing printer {printer_id}")
                await instance.control.pause()
            elif action == "stop":
                logger.info(f"Auto-stopping printer {printer_id}")
                await instance.control.stop()
        except Exception as e:
            logger.error(f"Failed to trigger {action} for {printer_id}: {e}")

