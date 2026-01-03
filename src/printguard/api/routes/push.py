from fastapi import APIRouter, Depends, Header

from ..deps import get_services
from ...core.db.session import ServiceManager
from ...core.db.schemas.interactions.push_subscriptions import (
    PushSubscriptionCreate,
    PushSubscriptionRead,
    PushUnsubscribeRequest,
)


router = APIRouter(prefix="/push")


@router.post("/subscribe", response_model=PushSubscriptionRead)
async def subscribe(
    data: PushSubscriptionCreate,
    services: ServiceManager = Depends(get_services),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
):
    if data.user_agent is None and user_agent:
        data.user_agent = user_agent
    return await services.push_subscriptions.upsert(data)


@router.post("/unsubscribe")
async def unsubscribe(
    data: PushUnsubscribeRequest,
    services: ServiceManager = Depends(get_services),
):
    await services.push_subscriptions.unsubscribe_by_endpoint(data.endpoint)
    return {"ok": True}
