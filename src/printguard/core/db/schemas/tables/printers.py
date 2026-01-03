import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates, object_session

from ...base import Base
from ...types import ComponentType
from .components import DeviceComponent

class Printer(Base):
    __tablename__ = "printers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    detection_majority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    camera_comp_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("device_components.id"))
    status_comp_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("device_components.id"))
    start_ctrl_comp_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("device_components.id"))
    stop_ctrl_comp_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("device_components.id"))

    camera_component: Mapped[Optional["DeviceComponent"]] = relationship(foreign_keys=[camera_comp_id])
    status_component: Mapped[Optional["DeviceComponent"]] = relationship(foreign_keys=[status_comp_id])
    start_control: Mapped[Optional["DeviceComponent"]] = relationship(foreign_keys=[start_ctrl_comp_id])
    stop_control: Mapped[Optional["DeviceComponent"]] = relationship(foreign_keys=[stop_ctrl_comp_id])

    @validates("camera_comp_id", "status_comp_id", "start_ctrl_comp_id", "stop_ctrl_comp_id")
    def validate_components(self, key: str, component_id: uuid.UUID) -> uuid.UUID:
        if component_id is None: return component_id
        session = object_session(self)
        if not session: return component_id

        expected_type = {
            "camera_comp_id": ComponentType.CAMERA,
            "status_comp_id": ComponentType.STATUS,
            "start_ctrl_comp_id": ComponentType.CONTROL,
            "stop_ctrl_comp_id": ComponentType.CONTROL,
        }.get(key)

        comp_type = session.execute(
            select(DeviceComponent.type).where(DeviceComponent.id == component_id)
        ).scalar()

        if comp_type and comp_type != expected_type:
            raise ValueError(f"Component {component_id} is {comp_type}, but {key} requires {expected_type}")
        return component_id