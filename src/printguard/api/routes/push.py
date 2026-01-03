from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.schemas.interactions.push_subscriptions import (
    PushSubscriptionCreate,
    PushSubscriptionRead,
    PushUnsubscribeRequest,
)
from ...core.security.jwt import TokenData


router = APIRouter(prefix="/push")


@router.post("/subscribe", response_model=PushSubscriptionRead)
async def subscribe(
    data: PushSubscriptionCreate,
    services: ServiceManager = Depends(get_services),
    current: TokenData = Depends(get_current_identity),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
):
    """Subscribe to push notifications. Requires authentication."""
    if data.user_agent is None and user_agent:
        data.user_agent = user_agent
    try:
        return await services.push_subscriptions.upsert(data, current.sub)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/unsubscribe")
async def unsubscribe(
    data: PushUnsubscribeRequest,
    services: ServiceManager = Depends(get_services),
    current: TokenData = Depends(get_current_identity),
):
    """Unsubscribe from push notifications. Requires auth; owner-only."""
    try:
        await services.push_subscriptions.unsubscribe(data.endpoint, current.sub)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return {"ok": True}
