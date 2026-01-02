import uuid
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..db.session import ServiceManager
    from ..db.schemas.tables.components import DeviceComponent
from ..db.base import BaseConfig
from ..state.models import PrintingState

class BaseConnection:
    """Base class for all connections."""

    _connection_config: BaseConfig
    connection_id: Optional[uuid.UUID]
    service_manager: Optional["ServiceManager"]
    
    def __init__(self, config: BaseConfig, connection_id: Optional[uuid.UUID] = None, service_manager: Optional["ServiceManager"] = None):
        self._connection_config = config
        self.connection_id = connection_id
        self.service_manager = service_manager

    async def is_healthy(self) -> bool:
        """Check if the connection is healthy."""
        raise NotImplementedError("The 'is_healthy' connection function has not been implemented.")

    async def get_camera_entities(self, camera_ids: Optional[List[str]]) -> List["DeviceComponent"]:
        """Get the cameras from the connection. 
        If camera_ids is provided, only return the cameras with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_cameras' connection function has not been implemented.")

    async def get_status_entities(self, status_ids: Optional[List[str]]) -> List["DeviceComponent"]:
        """Get the statuses from the connection. If status_ids is provided, only return the statuses with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_statuses' connection function has not been implemented.")

    async def get_control_entities(self, control_ids: Optional[List[str]]) -> List["DeviceComponent"]:
        """Get the controls from the connection. If control_ids is provided, only return the controls with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_controls' connection function has not been implemented.")

    async def trigger_control(self, control_id: str) -> bool:
        """Trigger the control with the given id.
        Returns True if the control was triggered successfully, False otherwise.
        """
        raise NotImplementedError("The 'trigger_control' connection function has not been implemented.")

    async def get_status_states(self, status_ids: Optional[List[str]]) -> List[str]:
        """Get the latest state of the status entities. If status_ids is provided, only return the statuses with the given ids.
        Returns a list of status states.
        """
        raise NotImplementedError("The 'get_status_states' connection function has not been implemented.")

    async def get_stream_url(self, component: "DeviceComponent") -> str:
        """Get the RTSP stream URL for a camera component."""
        raise NotImplementedError("The 'get_stream_url' connection function has not been implemented.")

    def map_status_state(self, state_str: str) -> PrintingState:
        """Map a raw state string from the connection to a PrintingState enum.
        Override in subclasses for connection-specific mapping logic.
        """
        state_lower = state_str.lower() if state_str else ""
        if "printing" in state_lower:
            return PrintingState.PRINTING
        elif "paused" in state_lower:
            return PrintingState.PAUSED
        elif "idle" in state_lower or "standby" in state_lower:
            return PrintingState.IDLE
        return PrintingState.OFFLINE