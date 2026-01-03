import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict
from ....connections import ConnectionConfig

class ConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    configuration: ConnectionConfig

class ConnectionCreate(BaseModel):
    name: str
    configuration: ConnectionConfig

class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    configuration: Optional[ConnectionConfig] = None