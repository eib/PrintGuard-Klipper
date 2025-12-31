from typing import Annotated, Union
from pydantic import Field, RootModel

from .homeassistant import HomeAssistantConnectionConfig

ConnectionConfig = Annotated[
    Union[HomeAssistantConnectionConfig, ],
    Field(discriminator="type")
]

class ConnectionConfigRoot(RootModel):
    root: ConnectionConfig