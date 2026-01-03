import uuid
from typing import List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.tables.printer_subscriptions import PrinterSubscription
from ..schemas.interactions.printer_subscriptions import PrinterSubscriptionCreate
from ...state.manager import GlobalStateManager
from ...state.models import WebSocketEvent, WebSocketEventUpdateType


class PrinterSubscriptionService:
    def __init__(self, session: AsyncSession, state_manager: GlobalStateManager):
        self.session = session
        self.state_manager = state_manager

    async def subscribe(self, identity_id: uuid.UUID, data: PrinterSubscriptionCreate) -> PrinterSubscription:
        existing = await self._get(identity_id, data.printer_id)
        if existing:
            return existing
        obj = PrinterSubscription(identity_id=identity_id, printer_id=data.printer_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        await self._emit(WebSocketEventUpdateType.CREATE, obj.id)
        return obj

    async def unsubscribe(self, identity_id: uuid.UUID, printer_id: uuid.UUID) -> bool:
        existing = await self._get(identity_id, printer_id)
        if not existing:
            return True
        await self.session.execute(
            delete(PrinterSubscription).where(PrinterSubscription.id == existing.id)
        )
        await self.session.commit()
        await self._emit(WebSocketEventUpdateType.DELETE, existing.id)
        return True

    async def list_for_identity(self, identity_id: uuid.UUID) -> List[PrinterSubscription]:
        result = await self.session.execute(
            select(PrinterSubscription).where(PrinterSubscription.identity_id == identity_id)
        )
        return list(result.scalars().all())

    async def _get(self, identity_id: uuid.UUID, printer_id: uuid.UUID) -> PrinterSubscription | None:
        result = await self.session.execute(
            select(PrinterSubscription).where(
                PrinterSubscription.identity_id == identity_id,
                PrinterSubscription.printer_id == printer_id,
            )
        )
        return result.scalar_one_or_none()

    async def _emit(self, update_type: WebSocketEventUpdateType, obj_id: uuid.UUID) -> None:
        await self.state_manager.send_update(update_type, WebSocketEvent.PRINTER_SUBSCRIPTION_UPDATE, str(obj_id))
