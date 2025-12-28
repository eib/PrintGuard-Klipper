from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    scopes: Mapped[str] = mapped_column(String(255), default="")

class M2MApplication(Base):
    __tablename__ = "m2m_applications"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    client_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_client_secret: Mapped[str] = mapped_column(String(255))
    scopes: Mapped[str] = mapped_column(String(255), default="")

class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    client_public_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Inference settings
    inference_sensitivity: Mapped[float] = mapped_column(default=1.0)
    inference_majority_voting: Mapped[int] = mapped_column(default=1)
    inference_target_fps: Mapped[float] = mapped_column(default=1000.0)
    detection_action: Mapped[str] = mapped_column(String(20), default="none")
    inference_paused: Mapped[bool] = mapped_column(default=False)
    
    component_links: Mapped[list["PrinterComponentLink"]] = relationship(back_populates="printer", cascade="all, delete-orphan")

class Connection(Base):
    __tablename__ = "connections"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    components: Mapped[list["Component"]] = relationship(back_populates="connection", cascade="all, delete-orphan")

class Component(Base):
    __tablename__ = "components"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(20))  # camera, control, status
    provider: Mapped[str] = mapped_column(String(50))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    connection_id: Mapped[str | None] = mapped_column(ForeignKey("connections.id"), nullable=True)
    entity_config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    connection: Mapped["Connection | None"] = relationship(back_populates="components")
    printer_links: Mapped[list["PrinterComponentLink"]] = relationship(back_populates="component", cascade="all, delete-orphan")

class PrinterComponentLink(Base):
    __tablename__ = "printer_component_links"
    
    printer_id: Mapped[str] = mapped_column(ForeignKey("printers.id"), primary_key=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    printer: Mapped["Printer"] = relationship(back_populates="component_links")
    component: Mapped["Component"] = relationship(back_populates="printer_links")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    endpoint: Mapped[str] = mapped_column(String(500), unique=True)
    p256dh: Mapped[str] = mapped_column(String(255))
    auth: Mapped[str] = mapped_column(String(255))

    user: Mapped["User"] = relationship()
    printer_subscriptions: Mapped[list["PrinterNotificationSubscription"]] = relationship(back_populates="push_subscription", cascade="all, delete-orphan")


class PrinterNotificationSubscription(Base):
    __tablename__ = "printer_notification_subscriptions"

    push_subscription_id: Mapped[int] = mapped_column(ForeignKey("push_subscriptions.id"), primary_key=True)
    printer_id: Mapped[str] = mapped_column(ForeignKey("printers.id"), primary_key=True)

    push_subscription: Mapped["PushSubscription"] = relationship(back_populates="printer_subscriptions")
    printer: Mapped["Printer"] = relationship()

