import uuid
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict

from ...types import ComponentType
from ....connections import (
    ConnectionCameraComponentConfig,
    ConnectionStatusComponentConfig,
    ConnectionControlComponentConfig
)
from .connections import ConnectionRead

class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: ComponentType
    config: Union[
            ConnectionCameraComponentConfig, 
            ConnectionStatusComponentConfig, 
            ConnectionControlComponentConfig
            ]
    connection: ConnectionRead

class ComponentCreate(BaseModel):
    type: ComponentType
    connection_id: uuid.UUID
    config: Union[
            ConnectionCameraComponentConfig, 
            ConnectionStatusComponentConfig, 
            ConnectionControlComponentConfig
            ]

class ComponentUpdate(BaseModel):
    config: Optional[Union[
            ConnectionCameraComponentConfig,
            ConnectionStatusComponentConfig,
            ConnectionControlComponentConfig
            ]] = None