from typing import Annotated, Union
from pydantic import Field, RootModel

from .homeassistant import HomeAssistantConnectionConfig, CameraComponentConfig, StatusComponentConfig, ControlComponentConfig

ConnectionConfig = Annotated[
    Union[HomeAssistantConnectionConfig, ],
    Field(discriminator="provider")
]

ConnectionCameraComponentConfig = Annotated[
    Union[CameraComponentConfig, ],
    Field(discriminator="provider")
]

ConnectionStatusComponentConfig = Annotated[
    Union[StatusComponentConfig, ],
    Field(discriminator="provider")
]

ConnectionControlComponentConfig = Annotated[
    Union[ControlComponentConfig, ],
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