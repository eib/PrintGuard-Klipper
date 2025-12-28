from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ...core.database import get_db
from ...core.db_models import PushSubscription, PrinterNotificationSubscription, Printer
from ...core.models import NotificationSubscriptionRequest, NotificationToggleRequest
from ...core.config import get_settings
from ..auth_utils import get_current_identity

router = APIRouter(prefix="/notifications", tags=["notifications"])
settings = get_settings()

@router.get("/vapid-public-key")
async def get_vapid_public_key():
    return {"public_key": settings.vapid_public_key}

@router.post("/subscribe")
async def subscribe(
    req: NotificationSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"])
):
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == req.subscription.endpoint
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"status": "already_subscribed"}

    sub = PushSubscription(
        user_id=user.id,
        endpoint=req.subscription.endpoint,
        p256dh=req.subscription.keys.get("p256dh"),
        auth=req.subscription.keys.get("auth")
    )
    db.add(sub)
    await db.commit()
    return {"status": "subscribed"}

@router.post("/unsubscribe")
async def unsubscribe(
    req: NotificationSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"])
):
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == req.subscription.endpoint
        )
    )
    await db.commit()
    return {"status": "unsubscribed"}

@router.put("/printer/{printer_id}")
async def toggle_printer_notifications(
    printer_id: str,
    req: NotificationToggleRequest,
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"])
):
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Printer not found")

    if req.enabled:
        result = await db.execute(
            select(PrinterNotificationSubscription).where(
                PrinterNotificationSubscription.user_id == user.id,
                PrinterNotificationSubscription.printer_id == printer_id
            )
        )
        if not result.scalar_one_or_none():
            sub = PrinterNotificationSubscription(user_id=user.id, printer_id=printer_id)
            db.add(sub)
    else:
        await db.execute(
            delete(PrinterNotificationSubscription).where(
                PrinterNotificationSubscription.user_id == user.id,
                PrinterNotificationSubscription.printer_id == printer_id
            )
        )
    
    await db.commit()
    return {"status": "updated", "enabled": req.enabled}

@router.post("/test/{printer_id}")
async def send_test_notification(
    printer_id: str,
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"])
):
    """Send a test notification to the current user for this printer."""
    from ...services.notifications import notify_defect
    notify_defect(printer_id, "Test Defect", 0.99)
    return {"status": "triggered"}

