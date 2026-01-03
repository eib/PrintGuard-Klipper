import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from ..schemas.tables.identities import Identity, User, ServiceAccount, IdentityScope
from ..schemas.interactions.identities import UserCreate, ServiceAccountCreate, IdentityUpdate
from ..types import IdentityType
from ...state.manager import GlobalStateManager
from ...state.models import WebSocketEvent, WebSocketEventUpdateType
from ...security.passwords import hash_password

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
            select(User)
            .where(User.username == username)
            .options(
                joinedload(User.identity).joinedload(Identity.scopes)
            )
        )
        return result.scalar_one_or_none()

    async def create_user(self, data: UserCreate) -> Identity:
        identity = Identity(type=IdentityType.USER)
        self.session.add(identity)
        await self.session.flush()
        user = User(
            identity_id=identity.id,
            username=data.username,
            password_hash=hash_password(data.password)
        )
        self.session.add(user)
        for scope_type in data.scopes:
            self.session.add(IdentityScope(identity_id=identity.id, scope=scope_type))
        await self.session.commit()
        await self.state_manager.send_update(WebSocketEventUpdateType.CREATE, self.websocket_event, str(identity.id))
        return await self.get_identity(identity.id)

    async def create_service_account(self, data: ServiceAccountCreate) -> Identity:
        """Creates a Machine-to-Machine (M2M) identity."""
        identity = Identity(type=IdentityType.SERVICE)
        self.session.add(identity)
        await self.session.flush()
        sa = ServiceAccount(
            identity_id=identity.id,
            client_secret_hash=hash_password(data.client_secret)
        )
        self.session.add(sa)
        for scope_type in data.scopes:
            self.session.add(IdentityScope(identity_id=identity.id, scope=scope_type))
        await self.session.commit()
        await self.state_manager.send_update(WebSocketEventUpdateType.CREATE, self.websocket_event, str(identity.id))
        return await self.get_identity(identity.id)

    async def update_identity(self, identity_id: uuid.UUID, data: IdentityUpdate) -> Optional[Identity]:
        """Handles partial updates for both Users and M2M Service Accounts."""
        identity = await self.get_identity(identity_id)
        if not identity:
            return None
        # Update linked User table
        if identity.user:
            if data.username is not None:
                identity.user.username = data.username
            if data.password is not None:
                identity.user.password_hash = hash_password(data.password)
        # Update linked ServiceAccount table
        if identity.service_account and data.client_secret is not None:
            identity.service_account.client_secret_hash = hash_password(data.client_secret)
        # Sync Scopes if provided
        if data.scopes is not None:
            await self.session.execute(delete(IdentityScope).where(IdentityScope.identity_id == identity_id))
            for scope_type in data.scopes:
                self.session.add(IdentityScope(identity_id=identity_id, scope=scope_type))
        await self.session.commit()
        await self.state_manager.send_update(WebSocketEventUpdateType.UPDATE, self.websocket_event, str(identity_id))
        return await self.get_identity(identity_id)
    
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