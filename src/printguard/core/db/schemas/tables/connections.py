import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, PydanticType
from ....connections import ConnectionConfig, ConnectionConfigRoot


class Connection(Base):
    __tablename__ = "connections"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[ConnectionConfig] = mapped_column(PydanticType(ConnectionConfigRoot))