"""SQLAlchemy models for the reports module."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ReportModel(Base):
    """Report metadata model."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    filter_params: Mapped[dict[str, str | int | None]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    file_format: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, nullable=False
    )
    generated_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str] = mapped_column(String, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<ReportModel(id={self.id!r}, type={self.report_type!r}, status={self.status!r})>"