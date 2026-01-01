import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from . import BaseService
from ..schemas.tables.components import DeviceComponent
from ..schemas.interactions.components import ComponentCreate
from ...state.manager import GlobalStateManager
from ...state.models import WebSocketEvent

class ComponentService(BaseService[DeviceComponent, ComponentCreate]):
    def __init__(self, session: AsyncSession, state_manager: GlobalStateManager):
        super().__init__(DeviceComponent, session, state_manager, WebSocketEvent.COMPONENT_UPDATE)

    async def get_full(self, id: uuid.UUID) -> DeviceComponent:
        return await self.get(id, load_relations=[DeviceComponent.connection])

    async def list_full(self) -> List[DeviceComponent]:
        return await self.list(load_relations=[DeviceComponent.connection])