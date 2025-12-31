import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Enum, ForeignKey, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base
from ...types import IdentityType, ScopeType

class Identity(Base):
    __tablename__ = "identities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[IdentityType] = mapped_column(Enum(IdentityType))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[Optional["User"]] = relationship(back_populates="identity", cascade="all, delete-orphan")
    service_account: Mapped[Optional["ServiceAccount"]] = relationship(back_populates="identity", cascade="all, delete-orphan")
    scopes: Mapped[List["IdentityScope"]] = relationship(back_populates="identity", cascade="all, delete-orphan")

class IdentityScope(Base):
    __tablename__ = "identity_scopes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[ScopeType] = mapped_column(Enum(ScopeType), nullable=False)
    identity: Mapped["Identity"] = relationship(back_populates="scopes")

class User(Base):
    __tablename__ = "users"
    identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="CASCADE"), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    identity: Mapped["Identity"] = relationship(back_populates="user")

class ServiceAccount(Base):
    __tablename__ = "service_accounts"
    identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="CASCADE"), primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    client_secret_hash: Mapped[str] = mapped_column(Text, nullable=False)
    identity: Mapped["Identity"] = relationship(back_populates="service_account")