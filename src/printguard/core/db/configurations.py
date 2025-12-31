from typing import Union, Literal, Annotated
from pydantic import BaseModel, Field, RootModel
from .types import ConnectionType, ComponentType

class BaseConfig(BaseModel):
    type: str

class OctoPrintConnectionConfig(BaseConfig):
    type: Literal[ConnectionType.OCTOPRINT] = ConnectionType.OCTOPRINT
    base_url: str
    api_key: str

class CameraComponentConfig(BaseConfig):
    type: Literal[ComponentType.CAMERA] = ComponentType.CAMERA
    # TODO: Other attributes for camera components

class ControlComponentConfig(BaseConfig):
    type: Literal[ComponentType.CONTROL] = ComponentType.CONTROL
    # TODO: Other attributes for control components

class StatusComponentConfig(BaseConfig):
    type: Literal[ComponentType.STATUS] = ComponentType.STATUS
    # TODO: Other attributes for status components

ConnectionConfig = Annotated[
    Union[OctoPrintConnectionConfig, ],
    Field(discriminator="type")
]

class ConnectionConfigRoot(RootModel):
    root: ConnectionConfig