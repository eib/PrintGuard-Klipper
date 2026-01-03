from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from ..core.db.session import AsyncSessionLocal, ServiceManager
from ..core.state.manager import state_manager

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_services(session: AsyncSession = Depends(get_db)) -> ServiceManager:
    return ServiceManager(session, state_manager)