from typing import Literal

from ..db.config import BaseConfig
from ..db.types import ConnectionType

class HomeAssistantConnectionConfig(BaseConfig):
    type: Literal[ConnectionType.HOMEASSISTANT] = ConnectionType.HOMEASSISTANT
    url: str
    api_key: str