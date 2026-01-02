from typing import Annotated, Union
from pydantic import Field, RootModel

from .homeassistant import (HomeAssistantConnectionConfig as HAConnectionConfig, 
                            CameraComponentConfig as HACameraComponentConfig, 
                            StatusComponentConfig as HAStatusComponentConfig, 
                            ControlComponentConfig as HAControlComponentConfig)


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