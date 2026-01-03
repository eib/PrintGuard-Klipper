from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.schemas.interactions.printer_subscriptions import (
    PrinterSubscriptionCreate,
    PrinterSubscriptionRead,
)
from ...core.security.jwt import TokenData

router = APIRouter(prefix="/push/printers")


@router.get("/", response_model=list[PrinterSubscriptionRead])
async def list_my_printer_subscriptions(
    services: ServiceManager = Depends(get_services),
    current: TokenData = Depends(get_current_identity),
):
    return await services.printer_subscriptions.list_for_identity(current.sub)


@router.post("/subscribe", response_model=PrinterSubscriptionRead)
async def subscribe_printer(
    data: PrinterSubscriptionCreate,
    services: ServiceManager = Depends(get_services),
    current: TokenData = Depends(get_current_identity),
):
    return await services.printer_subscriptions.subscribe(current.sub, data)


@router.post("/unsubscribe")
async def unsubscribe_printer(
    data: PrinterSubscriptionCreate,
    services: ServiceManager = Depends(get_services),
    current: TokenData = Depends(get_current_identity),
):
    await services.printer_subscriptions.unsubscribe(current.sub, data.printer_id)
    return {"ok": True}
