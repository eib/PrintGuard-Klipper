from typing import Literal, Optional, List, Dict, Any, TYPE_CHECKING
import uuid
from datetime import datetime
from httpx import RequestError
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..db.session import ServiceManager
    from ..db.schemas.tables.components import DeviceComponent

from ..db.base import BaseConfig
from ..db.types import ConnectionType, ComponentType
from ..state.models import PrintingState

from .base import BaseConnection
from ..networking import http_client, RequestParams, HTTPMethod, ResponseData

CAMERA_DOMAIN = "camera."
STATUS_DOMAIN = ("sensor.", "binary_sensor.")
CONTROL_DOMAIN = ("switch.", "light.", "button.", "input_button.", "lock.", "fan.", "cover.", "climate.")

class HomeAssistantConnectionConfig(BaseConfig):
    provider: Literal[ConnectionType.HOMEASSISTANT] = ConnectionType.HOMEASSISTANT
    url: str
    api_key: str

class HABaseComponentConfig(BaseModel):
    provider: Literal[ConnectionType.HOMEASSISTANT] = ConnectionType.HOMEASSISTANT 

class CameraComponentConfig(HABaseComponentConfig):
    entity_id: str
    brightness: float = Field(100.0, ge=0.0, le=500.0)
    contrast: float = Field(100.0, ge=0.0, le=500.0)
    sharpness: float = Field(100.0, ge=0.0, le=500.0)

class StatusComponentConfig(HABaseComponentConfig):
    entity_id: str
    is_printing_attr: str
    is_idle_attr: str
    attributes: List[str]

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

    async def is_healthy(self) -> bool:
        """Check if the HA API is running and the token is valid."""
        try:
            response: ResponseData = await http_client.run_async(
                params=RequestParams(
                    url=f"{self._connection_config.url}/api/",
                    method=HTTPMethod.GET,
                    headers=self.headers
                )
            )
            return response.is_success and response.content.get("message") == "API running."
        except Exception:
            return False

    def __init__(self, config: HomeAssistantConnectionConfig, connection_id: Optional[uuid.UUID] = None, service_manager: Optional["ServiceManager"] = None):
        super().__init__(config, connection_id, service_manager)
        self.headers = {
            "Authorization": f"Bearer {self._connection_config.api_key}",
            "Content-Type": "application/json"
        }

    async def _link_entities_to_db(self, components: List["DeviceComponent"], component_type: ComponentType):
        if self.service_manager and self.connection_id:
            db_components = await self.service_manager.components.get_by_connection(
                self.connection_id,
                component_type
            )
            existing_map = {c.config.get("entity_id"): c.id for c in db_components}
            for component in components:
                entity_id = component.config.get("entity_id")
                if entity_id in existing_map:
                    component.id = existing_map[entity_id]

    async def _get_raw_states(self) -> List[HAEntityState]:
        """Fetch all entity states from the HA instance."""
        response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/states",
                method=HTTPMethod.GET,
                headers=self.headers
            )
        )
        if response.is_success and response.status_code == 200:
            return [HAEntityState(**entity) for entity in response.content]
        else:
            raise RequestError(f"Failed to get entities. Status: {response.status_code}")

    async def get_camera_entities(self, camera_ids: Optional[List[str]] = None) -> List["DeviceComponent"]:
        """Identifies cameras by their domain prefix."""
        from ..db.schemas.tables.components import DeviceComponent
        states = await self._get_raw_states()
        cameras = [s for s in states if s.entity_id.startswith(CAMERA_DOMAIN)]
        if camera_ids:
            cameras = [c for c in cameras if c.entity_id in camera_ids]
        components = [
            DeviceComponent(
                type=ComponentType.CAMERA,
                config=CameraComponentConfig(entity_id=c.entity_id).model_dump()
            ) for c in cameras
        ]
        await self._link_entities_to_db(components, ComponentType.CAMERA)
        return components

    async def get_status_entities(self, status_ids: Optional[List[str]] = None) -> List["DeviceComponent"]:
        """Identifies statuses by their domain prefix."""
        from ..db.schemas.tables.components import DeviceComponent
        states = await self._get_raw_states()
        statuses = [s for s in states if s.entity_id.startswith(STATUS_DOMAIN)]
        if status_ids:
            statuses = [s for s in statuses if s.entity_id in status_ids]
            
        components = [
            DeviceComponent(
                type=ComponentType.STATUS,
                config=StatusComponentConfig(
                    entity_id=s.entity_id,
                    is_printing_attr="",
                    is_idle_attr="",
                    attributes=[s.state] + list(s.attributes.keys())
                ).model_dump()
            ) for s in statuses
        ]

        await self._link_entities_to_db(components, ComponentType.STATUS)
        return components

    async def get_control_entities(self, control_ids: Optional[List[str]] = None) -> List["DeviceComponent"]:
        """Identifies controls by their domain prefix."""
        from ..db.schemas.tables.components import DeviceComponent
        states = await self._get_raw_states()
        controls = [s for s in states if s.entity_id.startswith(CONTROL_DOMAIN)]
        if control_ids:
            controls = [c for c in controls if c.entity_id in control_ids]
            
        components = [
            DeviceComponent(
                type=ComponentType.CONTROL,
                config=ControlComponentConfig(entity_id=c.entity_id).model_dump()
            ) for c in controls
        ]

        await self._link_entities_to_db(components, ComponentType.CONTROL)
        return components

    async def trigger_control(self, control_id: str) -> bool:
        """Triggers the appropriate service based on entity domain."""
        domain = control_id.split(".")[0]
        service_map = {
            "button": "press",
            "input_button": "press",
            "lock": "toggle",
            "light": "toggle",
            "switch": "toggle",
            "fan": "toggle",
            "cover": "toggle"
        }
        service = service_map.get(domain, "toggle")
        response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/services/{domain}/{service}",
                method=HTTPMethod.POST,
                headers=self.headers,
                json_data={"entity_id": control_id}
            )
        )
        return response.is_success and response.status_code == 200

    async def get_status_states(self, status_ids: Optional[List[str]] = None) -> List[str]:
        """Retrieves the current state strings for the specified IDs."""
        states = await self._get_raw_states()
        if status_ids:
            state_map = {s.entity_id: s.state for s in states}
            return [state_map.get(sid, "unknown") for sid in status_ids]
        return [s.state for s in states if s.entity_id.startswith(STATUS_DOMAIN)]

    async def get_stream_url(self, component: "DeviceComponent") -> str:
        """Get the MJPEG proxy stream URL for a camera entity.
        
        Returns the authenticated MJPEG proxy URL using the camera's access_token
        from entity state attributes. This URL can be ingested by MediaMTX.
        """
        entity_id = component.config.get("entity_id")
        if not entity_id:
            raise ValueError("Component config missing entity_id")
        state_response: ResponseData = await http_client.run_async(
            params=RequestParams(
                url=f"{self._connection_config.url}/api/states/{entity_id}",
                method=HTTPMethod.GET,
                headers=self.headers
            )
        )
        if not state_response.is_success:
            raise ValueError(f"Could not fetch state for {entity_id}")
        attributes = state_response.content.get("attributes", {})
        access_token = attributes.get("access_token")
        if not access_token:
            raise ValueError(f"No access_token found for camera {entity_id}")
        return f"{self._connection_config.url}/api/camera_proxy_stream/{entity_id}?token={access_token}"

    def map_status_state(self, state_str: str, config: Optional[StatusComponentConfig] = None) -> PrintingState:
        """Map Home Assistant state string to PrintingState using component config."""
        if config and config.is_printing_attr and state_str == config.is_printing_attr:
            return PrintingState.PRINTING
        return PrintingState.IDLE