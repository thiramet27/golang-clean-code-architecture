"""SQLAlchemy tables. These are adapters, not domain entities: the domain never imports them."""

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    # Columns never returned by the generic /data API (Go: `json:"-"`)
    hidden_fields: ClassVar[frozenset[str]] = frozenset()


class UserModel(Base):
    __tablename__ = "users"
    hidden_fields = frozenset({"password"})

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), default="")
    password: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserTokenModel(Base):
    __tablename__ = "user_tokens"
    hidden_fields = frozenset({"access", "refresh"})

    id: Mapped[int] = mapped_column(primary_key=True)
    # One session per user, same behaviour as the Go version (UpsertOAuth by user_id)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    access: Mapped[str] = mapped_column(String(64))  # sha256 hex digest, not the raw token
    refresh: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[UserModel] = relationship(lazy="raise")


class UserPermissionModel(Base):
    __tablename__ = "user_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    permission: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
