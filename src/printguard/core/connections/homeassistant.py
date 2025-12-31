from typing import Literal
from pydantic import BaseModel

from ..db.config import BaseConfig
from ..db.types import ConnectionType

class HomeAssistantConnectionConfig(BaseConfig):
    provider: Literal[ConnectionType.HOMEASSISTANT] = ConnectionType.HOMEASSISTANT
    url: str
    api_key: str

class HABaseComponentConfig(BaseModel):
    provider: Literal[ConnectionType.HOMEASSISTANT] = ConnectionType.HOMEASSISTANT 

class CameraComponentConfig(HABaseComponentConfig):
    entity_id: str

class StatusComponentConfig(HABaseComponentConfig):
    entity_id: str
    is_printing_attr: str
    is_idle_attr: str

class ControlComponentConfig(HABaseComponentConfig):
    entity_id: str