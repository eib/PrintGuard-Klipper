from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .services.printers import PrinterService
from .services.components import ComponentService
from .services.identities import IdentityService
from .services.connections import ConnectionService

from ..config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class ServiceManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.printers = PrinterService(session)
        self.components = ComponentService(session)
        self.identities = IdentityService(session)
        self.connections = ConnectionService(session)

@asynccontextmanager
async def get_session_ctx() -> AsyncGenerator[ServiceManager, None]:
    async with AsyncSessionLocal() as session:
        yield ServiceManager(session)