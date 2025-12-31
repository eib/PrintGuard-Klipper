import uuid
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from ...base import Base
from ...types import ComponentType
from ...configurations import BaseConfig, CameraComponentConfig, ControlComponentConfig, StatusComponentConfig
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
        model_map = {
            ComponentType.CAMERA: CameraComponentConfig,
            ComponentType.CONTROL: ControlComponentConfig,
            ComponentType.STATUS: StatusComponentConfig,
        }
        target_model = model_map.get(self.type)
        if isinstance(value, dict) and target_model:
            value["type"] = self.type.value
            return target_model.model_validate(value)
        if target_model and not isinstance(value, target_model):
            raise ValueError(f"Config must be {target_model.__name__} for type {self.type}")
        return value