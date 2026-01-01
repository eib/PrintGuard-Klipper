import uuid
from typing import Any, List, Optional
from ..db.services.components import ComponentService

from ..db.schemas.tables.components import DeviceComponent
from ..db.base import BaseConfig

class BaseConnection:
    """Base class for all connections."""

    _connection_config: BaseConfig
    connection_id: Optional[uuid.UUID]
    component_service: Optional[ComponentService]
    
    def __init__(self, config: BaseConfig, connection_id: Optional[uuid.UUID] = None, component_service: Optional[ComponentService] = None):
        self._connection_config = config
        self.connection_id = connection_id
        self.component_service = component_service

    async def is_healthy(self) -> bool:
        """Check if the connection is healthy."""
        raise NotImplementedError("The 'is_healthy' connection function has not been implemented.")

    async def get_camera_entities(self, camera_ids: Optional[List[str]]) -> List[DeviceComponent]:
        """Get the cameras from the connection. 
        If camera_ids is provided, only return the cameras with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_cameras' connection function has not been implemented.")

    async def get_status_entities(self, status_ids: Optional[List[str]]) -> List[DeviceComponent]:
        """Get the statuses from the connection. If status_ids is provided, only return the statuses with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_statuses' connection function has not been implemented.")

    async def get_control_entities(self, control_ids: Optional[List[str]]) -> List[DeviceComponent]:
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