from typing import Literal
from pydantic import BaseModel
from .types import ComponentType

class BaseConfig(BaseModel):
    type: str

class CameraComponentConfig(BaseConfig):
    type: Literal[ComponentType.CAMERA] = ComponentType.CAMERA
    # TODO: Other attributes for camera components

class ControlComponentConfig(BaseConfig):
    type: Literal[ComponentType.CONTROL] = ComponentType.CONTROL
    # TODO: Other attributes for control components

class StatusComponentConfig(BaseConfig):
    type: Literal[ComponentType.STATUS] = ComponentType.STATUS
    # TODO: Other attributes for status components