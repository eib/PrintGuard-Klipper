import uuid
from datetime import datetime
from sqlalchemy import UniqueConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class PrinterSubscription(Base):
    __tablename__ = "printer_subscriptions"
    __table_args__ = (
        UniqueConstraint("identity_id", "printer_id", name="uq_printer_subscription_identity_printer"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    printer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("printers.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
