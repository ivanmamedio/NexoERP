"""SQLAlchemy models for the audit module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class AuditLogModel(Base):
    """Immutable append-only audit log table."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    before: Mapped[str] = mapped_column(String, nullable=False, default="{}")
    after: Mapped[str] = mapped_column(String, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AuditLogModel(id={self.id!r}, action={self.action!r})>"
