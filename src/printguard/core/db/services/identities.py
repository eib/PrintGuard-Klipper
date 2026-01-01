import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from ..schemas.tables.identities import Identity, User, IdentityScope
from ..schemas.interactions.identities import UserCreate
from ..types import IdentityType
from ...state.manager import GlobalStateManager
from ...state.models import WebSocketEvent, WebSocketEventUpdateType

class IdentityService:
    """Manages the complex multi-table structure of Identities, Users, and Scopes."""
    def __init__(self, session: AsyncSession, state_manager: GlobalStateManager):
        self.session = session
        self.state_manager = state_manager
        self.websocket_event = WebSocketEvent.IDENTITY_UPDATE

    async def get_identity(self, identity_id: uuid.UUID) -> Optional[Identity]:
        result = await self.session.execute(
            select(Identity)
            .where(Identity.id == identity_id)
            .options(joinedload(Identity.user), joinedload(Identity.service_account), joinedload(Identity.scopes))
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username).options(joinedload(User.identity))
        )
        return result.scalar_one_or_none()

    async def create_user(self, data: UserCreate) -> Identity:
        identity = Identity(type=IdentityType.USER)
        self.session.add(identity)
        await self.session.flush()

        user = User(
            identity_id=identity.id,
            username=data.username,
            password_hash=f"pbkdf2:{data.password}" 
        )
        self.session.add(user)

        for scope_type in data.scopes:
            scope = IdentityScope(identity_id=identity.id, scope=scope_type)
            self.session.add(scope)

        await self.session.commit()
        await self.state_manager.send_update(WebSocketEventUpdateType.CREATE, self.websocket_event, str(identity.id))
        return await self.get_identity(identity.id)
    
    async def delete_identity(self, identity_id: uuid.UUID) -> bool:
        await self.session.execute(delete(Identity).where(Identity.id == identity_id))
        await self.session.commit()
        await self.state_manager.send_update(WebSocketEventUpdateType.DELETE, self.websocket_event, str(identity_id))
        return True

    async def list_identities(self) -> List[Identity]:
        result = await self.session.execute(
            select(Identity).options(joinedload(Identity.user), joinedload(Identity.scopes))
        )
        return list(result.scalars().all())