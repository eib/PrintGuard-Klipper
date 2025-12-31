import uuid
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from ...base import Base
from ...types import ComponentType
from ...config import BaseConfig, CameraComponentConfig, ControlComponentConfig, StatusComponentConfig
from ....connections import (
    ConnectionCameraComponentConfigRoot,
    ConnectionStatusComponentConfigRoot,
    ConnectionControlComponentConfigRoot
)
from .connections import Connection

class DeviceComponent(Base):
    __tablename__ = "device_components"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[ComponentType] = mapped_column(Enum(ComponentType), nullable=False)
    connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("connections.id"))
    config: Mapped[BaseConfig] = mapped_column(JSONB)
    connection: Mapped["Connection"] = relationship()

    @validates("config")
    def validate_config_type(self, key, value):
        root_map = {
            ComponentType.CAMERA: ConnectionCameraComponentConfigRoot,
            ComponentType.CONTROL: ConnectionControlComponentConfigRoot,
            ComponentType.STATUS: ConnectionStatusComponentConfigRoot,
        }
        target_root = root_map.get(self.type)
        if target_root:
            return target_root.model_validate(value).model_dump()
        return value