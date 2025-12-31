import uuid
from typing import Generic, TypeVar, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from ..base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType]):
    """Base class for handling common async CRUD operations."""
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID, load_relations: list = None) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        if load_relations:
            for rel in load_relations:
                query = query.options(joinedload(rel))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(self, load_relations: list = None) -> List[ModelType]:
        query = select(self.model)
        if load_relations:
            for rel in load_relations:
                query = query.options(joinedload(rel))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, data: CreateSchemaType) -> ModelType:
        obj = self.model(**data.model_dump())
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: uuid.UUID, data: dict) -> Optional[ModelType]:
        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**data)
        )
        await self.session.commit()
        return await self.get(id)

    async def delete(self, id: uuid.UUID) -> bool:
        await self.session.execute(delete(self.model).where(self.model.id == id))
        await self.session.commit()
        return True