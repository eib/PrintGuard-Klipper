import uuid
from pydantic import BaseModel, ConfigDict

from ...configurations import BaseConfig
from ...types import ComponentType
from .connections import ConnectionRead

class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: ComponentType
    config: BaseConfig
    connection: ConnectionRead

class ComponentCreate(BaseModel):
    type: ComponentType
    connection_id: uuid.UUID
    config: BaseConfig