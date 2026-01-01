from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .base import Base
from ..config import settings
from ..state.manager import state_manager, GlobalStateManager
from .services.printers import PrinterService
from .services.components import ComponentService
from .services.identities import IdentityService
from .services.connections import ConnectionService
from .schemas.tables import connections, components, printers, identities

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Create tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class ServiceManager:
    def __init__(self, session: AsyncSession, state_manager: GlobalStateManager):
        self.session = session
        self.state_manager = state_manager
        self.printers = PrinterService(session, self.state_manager)
        self.components = ComponentService(session, self.state_manager)
        self.identities = IdentityService(session, self.state_manager)
        self.connections = ConnectionService(session, self.state_manager)

@asynccontextmanager
async def get_session_ctx() -> AsyncGenerator[ServiceManager, None]:
    async with AsyncSessionLocal() as session:
        yield ServiceManager(session, state_manager)