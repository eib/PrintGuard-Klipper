from sqlalchemy.orm import DeclarativeBase
from typing import Type
from pydantic import BaseModel
from sqlalchemy import TypeDecorator, JSON

class Base(DeclarativeBase):
    pass

class PydanticType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, pydantic_model: Type[BaseModel], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pydantic_model = pydantic_model

    def process_bind_param(self, value, dialect):
        if value is None: return None
        if isinstance(value, dict):
            return self.pydantic_model.model_validate(value).model_dump()
        return value.model_dump()

    def process_result_value(self, value, dialect):
        if value is None: return None
        return self.pydantic_model.model_validate(value)