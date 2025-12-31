from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import BaseService
from ..schemas.tables.connections import Connection
from ..schemas.interactions.connections import ConnectionCreate

class ConnectionService(BaseService[Connection, ConnectionCreate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Connection, session)

    async def get_by_name(self, name: str) -> Connection:
        result = await self.session.execute(select(Connection).where(Connection.name == name))
        return result.scalar_one_or_none()