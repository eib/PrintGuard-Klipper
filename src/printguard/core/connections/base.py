from typing import List, Optional

from ..db.schemas.tables.components import DeviceComponent

class BaseConnection:
    """Base class for all connections."""
    
    def __init__(self):
        ...

    async def is_healthy(self) -> bool:
        """Check if the connection is healthy."""
        raise NotImplementedError("The 'is_healthy' connection function has not been implemented.")

    async def get_cameras(self, camera_ids: Optional[List[str]]) -> List[DeviceComponent]:
        """Get the cameras from the connection. 
        If camera_ids is provided, only return the cameras with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_cameras' connection function has not been implemented.")

    async def get_statuses(self, status_ids: Optional[List[str]]) -> List[DeviceComponent]:
        """Get the statuses from the connection. If status_ids is provided, only return the statuses with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_statuses' connection function has not been implemented.")

    async def get_controls(self, control_ids: Optional[List[str]]) -> List[DeviceComponent]:
        """Get the controls from the connection. If control_ids is provided, only return the controls with the given ids.
        Returns a list of DeviceComponent objects with the connection's specific config.
        """
        raise NotImplementedError("The 'get_controls' connection function has not been implemented.")

    async def trigger_control(self, control_id: str) -> bool:
        """Trigger the control with the given id.
        Returns True if the control was triggered successfully, False otherwise.
        """
        raise NotImplementedError("The 'trigger_control' connection function has not been implemented.")