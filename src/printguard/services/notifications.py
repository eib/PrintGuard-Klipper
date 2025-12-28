import json
import asyncio
import logging
import os
from pywebpush import webpush, WebPushException
from sqlalchemy import select
from ..core.database import async_session as SessionLocal
from ..core.db_models import User, PushSubscription, PrinterNotificationSubscription
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def send_push_notification(subscription, payload):
    """Send push notification to a single subscription."""
    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning("VAPID keys not configured, cannot send push notification")
        return False
        
    try:
        await asyncio.to_thread(
            webpush,
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": "mailto:admin@example.com"}
        )
        return True
    except WebPushException as ex:
        logger.error(f"Web push failed: {ex}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in web push: {e}")
        return False

def notify_defect(session_id: str, defect_class: str, confidence: float, screenshot_path: str = None):
    """Send notifications when defect is detected. Triggers async task."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_notify_defect_async(session_id, defect_class, confidence, screenshot_path))
    except RuntimeError:
        logger.error("No running event loop to send notifications")

async def _notify_defect_async(session_id: str, defect_class: str, confidence: float, screenshot_path: str = None):
    """Async implementation of notify_defect."""
    from .streams import stream_manager
    source = stream_manager.get_source(session_id)
    printer_id = source.printer_id if source else session_id
    printer_name = source.device_name if source else "Printer"

    logger.info(f"Notification triggered for printer {printer_id} (session {session_id})")

    async with SessionLocal() as db:
        result = await db.execute(
            select(PushSubscription)
            .join(PrinterNotificationSubscription)
            .where(
                PrinterNotificationSubscription.printer_id == printer_id,
                PushSubscription.endpoint.is_not(None),
                PushSubscription.p256dh.is_not(None),
                PushSubscription.auth.is_not(None)
            )
        )
        subscriptions = result.scalars().all()
        
        if not subscriptions and session_id != printer_id:
            result = await db.execute(
                select(PushSubscription)
                .join(PrinterNotificationSubscription)
                .where(
                    PrinterNotificationSubscription.printer_id == session_id,
                    PushSubscription.endpoint.is_not(None),
                    PushSubscription.p256dh.is_not(None),
                    PushSubscription.auth.is_not(None)
                )
            )
            subscriptions = result.scalars().all()

        if not subscriptions:
            logger.info(f"No active device subscriptions found for printer {printer_id}")
            return

        logger.info(f"Found {len(subscriptions)} active device subscriptions for printer {printer_id}")

        image_url = None
        base_url = settings.last_known_public_base_url or ""
        
        if screenshot_path:
            filename = os.path.basename(screenshot_path)
            path = f"/screenshots/{filename}"
            image_url = f"{base_url}{path}" if base_url else path

        payload = {
            "title": "Print Error Detected",
            "body": f"{printer_name}: {defect_class} ({confidence:.0%} confidence)",
            "image": image_url,
            "data": {
                "printer_id": printer_id,
                "url": base_url or "/" 
            }
        }

        tasks = [send_push_notification(sub, payload) for sub in subscriptions]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        logger.info(f"Sent {success_count}/{len(subscriptions)} push notifications for printer {printer_id}")

async def notify_user_camera_access(user_id: int, camera_name: str):
    """Notify all devices of a user that someone wants to access their camera."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.endpoint.is_not(None),
                PushSubscription.p256dh.is_not(None),
                PushSubscription.auth.is_not(None)
            )
        )
        subscriptions = result.scalars().all()
        
        if not subscriptions:
            logger.info(f"No active device subscriptions found for user {user_id}")
            return

        logger.info(f"Found {len(subscriptions)} active device subscriptions for user {user_id}")

        base_url = settings.last_known_public_base_url or ""
        payload = {
            "title": "Camera Access Requested",
            "body": f"Someone wants to access your camera '{camera_name}'. Please open PrintGuard on the host device to start the stream.",
            "data": {
                "url": base_url or "/" 
            }
        }

        tasks = [send_push_notification(sub, payload) for sub in subscriptions]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        logger.info(f"Sent {success_count}/{len(subscriptions)} push notifications for user {user_id}")
