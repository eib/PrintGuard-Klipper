from typing import Annotated, Union, Optional, TYPE_CHECKING
from pydantic import Field, RootModel

from .homeassistant import (HomeAssistantConnectionConfig as HAConnectionConfig, 
                            CameraComponentConfig as HACameraComponentConfig, 
                            StatusComponentConfig as HAStatusComponentConfig, 
                            ControlComponentConfig as HAControlComponentConfig,
                            HomeAssistantConnection)
from .base import BaseConnection
from ..db.types import ConnectionType

if TYPE_CHECKING:
    from ..db.schemas.tables.connections import Connection
    from ..db.session import ServiceManager


def get_connection_instance(conn: "Connection", services: Optional["ServiceManager"] = None) -> Optional[BaseConnection]:
    """Instantiate a BaseConnection subclass from a DB Connection record."""
    config = conn.configuration.root if hasattr(conn.configuration, 'root') else conn.configuration
    if config.provider == ConnectionType.HOMEASSISTANT:
        return HomeAssistantConnection(config, conn.id, services)
    return None


ConnectionConfig = Annotated[
    Union[HAConnectionConfig, ],
    Field(discriminator="provider")
]

ConnectionCameraComponentConfig = Annotated[
    Union[HACameraComponentConfig, ],
    Field(discriminator="provider")
]

ConnectionStatusComponentConfig = Annotated[
    Union[HAStatusComponentConfig, ],
    Field(discriminator="provider")
]

ConnectionControlComponentConfig = Annotated[
    Union[HAControlComponentConfig, ],
    Field(discriminator="provider")
]

class ConnectionConfigRoot(RootModel):
    root: ConnectionConfig

class ConnectionCameraComponentConfigRoot(RootModel):
    root: ConnectionCameraComponentConfig

class ConnectionStatusComponentConfigRoot(RootModel):
    root: ConnectionStatusComponentConfig

class ConnectionControlComponentConfigRoot(RootModel):
    root: ConnectionControlComponentConfig