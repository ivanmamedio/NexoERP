"""Declarative base and timestamp mixin for SQLAlchemy models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class Base(DeclarativeBase):
    """Project-wide declarative base."""


class TimestampMixin:
    """Colunas created_at/updated_at padronizadas (UTC aware) para modelos SQLAlchemy."""

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
