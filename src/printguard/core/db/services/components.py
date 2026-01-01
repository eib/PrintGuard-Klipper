import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import BaseService
from ..schemas.tables.components import DeviceComponent
from ..types import ComponentType
from ..schemas.interactions.components import ComponentCreate
from ...state.manager import GlobalStateManager
from ...state.models import WebSocketEvent

class ComponentService(BaseService[DeviceComponent, ComponentCreate]):
    def __init__(self, session: AsyncSession, state_manager: GlobalStateManager):
        super().__init__(DeviceComponent, session, state_manager, WebSocketEvent.COMPONENT_UPDATE)

    async def get_by_connection(self, connection_id: uuid.UUID, component_type: Optional[ComponentType] = None) -> List[DeviceComponent]:
        query = select(DeviceComponent).where(DeviceComponent.connection_id == connection_id)
        if component_type:
            query = query.where(DeviceComponent.type == component_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_full(self, id: uuid.UUID) -> DeviceComponent:
        return await self.get(id, load_relations=[DeviceComponent.connection])

    async def list_full(self) -> List[DeviceComponent]:
        return await self.list(load_relations=[DeviceComponent.connection])