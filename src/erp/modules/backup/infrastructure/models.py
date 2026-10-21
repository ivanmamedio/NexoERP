"""SQLAlchemy models for the backup module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class BackupModel(Base):
    """Backup metadata model."""

    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backup_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(String, nullable=False, default="")
    source_db_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    rotation_tag: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<BackupModel(id={self.id!r}, type={self.backup_type!r}, status={self.status!r})>"
