import logging
import uuid
from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.tables.device_push_subscriptions import DevicePushSubscription
from ..schemas.interactions.push_subscriptions import PushSubscriptionCreate
from ...notifications.webpush import WebPushClient, WebPushSendResult
from ...notifications.models import PushPayloadBase
from ...notifications.vapid import ensure_vapid_configured
from ...state.manager import GlobalStateManager
from ...state.models import WebSocketEvent, WebSocketEventUpdateType

logger = logging.getLogger(__name__)


class PushSubscriptionService:
    def __init__(self, session: AsyncSession, state_manager: GlobalStateManager):
        self.session = session
        self.state_manager = state_manager

    async def upsert(
        self,
        data: PushSubscriptionCreate,
        identity_id: uuid.UUID,
    ) -> DevicePushSubscription:
        """Create or update a push subscription. Requires authenticated identity."""
        existing = await self._get_by_endpoint(data.endpoint)
        if existing:
            # Only owner can update their subscription
            if existing.identity_id != identity_id:
                raise PermissionError("Subscription belongs to another user")

            existing.p256dh = data.keys.p256dh
            existing.auth = data.keys.auth
            existing.expiration_time_ms = data.expiration_time_ms
            existing.user_agent = data.user_agent
            await self.session.commit()
            await self.session.refresh(existing)
            await self.state_manager.send_update(
                WebSocketEventUpdateType.UPDATE,
                WebSocketEvent.PUSH_SUBSCRIPTION_UPDATE,
                str(existing.id),
            )
            return existing

        obj = DevicePushSubscription(
            identity_id=identity_id,
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
            expiration_time_ms=data.expiration_time_ms,
            user_agent=data.user_agent,
        )
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        await self.state_manager.send_update(
            WebSocketEventUpdateType.CREATE,
            WebSocketEvent.PUSH_SUBSCRIPTION_UPDATE,
            str(obj.id),
        )
        return obj

    async def unsubscribe(self, endpoint: str, identity_id: uuid.UUID) -> bool:
        """Delete a subscription. Only the owner can delete their subscription."""
        existing = await self._get_by_endpoint(endpoint)
        if not existing:
            return True

        # Ownership check: only owner can delete
        if existing.identity_id != identity_id:
            raise PermissionError("Cannot delete subscription owned by another user")

        await self.session.execute(
            delete(DevicePushSubscription).where(DevicePushSubscription.id == existing.id)
        )
        await self.session.commit()
        await self.state_manager.send_update(
            WebSocketEventUpdateType.DELETE,
            WebSocketEvent.PUSH_SUBSCRIPTION_UPDATE,
            str(existing.id),
        )
        return True

    async def list_all(self) -> List[DevicePushSubscription]:
        result = await self.session.execute(select(DevicePushSubscription))
        return list(result.scalars().all())

    async def send_to_all(self, payload: PushPayloadBase) -> WebPushSendResult:
        keys = ensure_vapid_configured()
        if not keys:
            logger.debug("WebPush not configured; skipping send")
            return WebPushSendResult(sent=0, failed=0, deleted=0)

        client = WebPushClient(
            vapid_private_key=keys.private_key,
            vapid_subject=keys.subject,
        )

        subs = await self.list_all()
        payload_json = payload.model_dump_json()
        sent = 0
        failed = 0
        deleted = 0

        for sub in subs:
            try:
                result = await client.send(
                    endpoint=sub.endpoint,
                    p256dh=sub.p256dh,
                    auth=sub.auth,
                    payload_json=payload_json,
                )
                if result.ok:
                    sent += 1
                    continue

                failed += 1
                if result.should_delete:
                    await self.session.execute(
                        delete(DevicePushSubscription).where(DevicePushSubscription.id == sub.id)
                    )
                    deleted += 1
                    await self.state_manager.send_update(
                        WebSocketEventUpdateType.DELETE,
                        WebSocketEvent.PUSH_SUBSCRIPTION_UPDATE,
                        str(sub.id),
                    )
            except Exception:
                failed += 1
                logger.exception("WebPush send failed")

        if deleted:
            await self.session.commit()

        return WebPushSendResult(sent=sent, failed=failed, deleted=deleted)

    async def _get_by_endpoint(self, endpoint: str) -> Optional[DevicePushSubscription]:
        result = await self.session.execute(
            select(DevicePushSubscription).where(DevicePushSubscription.endpoint == endpoint)
        )
        return result.scalar_one_or_none()
