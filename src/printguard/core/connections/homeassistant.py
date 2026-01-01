from typing import Literal
from pydantic import BaseModel

from ..db.base import BaseConfig
from ..db.types import ConnectionType
from .base import BaseConnection
from ..networking import http_client, RequestParams, HTTPMethod, ResponseData

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

class HomeAssistantConnection(BaseConnection):

    _connection_config: HomeAssistantConnectionConfig
    headers: dict

    def __init__(self, config: HomeAssistantConnectionConfig):
        self._connection_config = config
        self.headers = {"Authorization": f"Bearer {self._connection_config.api_key}"}

    async def is_healthy(self) -> bool:
        response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/health",
                method=HTTPMethod.GET,
                headers=self.headers,
                params=None,
                json_data=None
            )
        )
        return response.is_success