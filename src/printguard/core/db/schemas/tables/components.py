import uuid
from sqlalchemy import Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from ...base import Base, BaseConfig
from ...types import ComponentType
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
    config: Mapped[BaseConfig] = mapped_column(JSON)
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