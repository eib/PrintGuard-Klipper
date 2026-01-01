from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from httpx import RequestError
from pydantic import BaseModel

from ..db.base import BaseConfig
from ..db.types import ConnectionType
from ..db.schemas.tables.components import DeviceComponent
from ..db.types import ComponentType
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

class HAContext(BaseModel):
    id: str
    parent_id: Optional[str] = None
    user_id: Optional[str] = None

class HAEntityState(BaseModel):
    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: datetime
    last_updated: datetime
    context: HAContext

class HomeAssistantConnection(BaseConnection):

    _connection_config: HomeAssistantConnectionConfig
    headers: dict

    def __init__(self, config: HomeAssistantConnectionConfig):
        self._connection_config = config
        self.headers = {"Authorization": f"Bearer {self._connection_config.api_key}"}

    async def is_healthy(self) -> bool:
        response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/",
                method=HTTPMethod.GET,
                headers=self.headers,
                params=None,
                json_data=None
            )
        )
        return response.content.get("message") == "API running." and response.is_success and response.status_code == 200

    async def _get_entities(self) -> List[DeviceComponent]:
        response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/states",
                method=HTTPMethod.GET,
                headers=self.headers,
                params=None,
                json_data=None
            )
        )
        if response.is_success and response.status_code == 200:
            return [HAEntityState(**entity) for entity in response.content]
        else:
            raise RequestError(f"Failed to get entities. Status code: {response.status_code}, Content: {response.content}")

    async def _get_entity(self, entity_id: str) -> HAEntityState:
        response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/states/{entity_id}",
                method=HTTPMethod.GET,
                headers=self.headers,
                params=None,
                json_data=None
            )
        )
        if response.is_success and response.status_code == 200:
            return HAEntityState(**response.content)
        else:
            raise RequestError(f"Failed to get entity. Status code: {response.status_code}, Content: {response.content}")