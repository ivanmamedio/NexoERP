"""SQLAlchemy models for the treasury module."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime


def _utcnow() -> datetime:
    return datetime.now(UTC)


class FinancialEntryModel(Base):
    """Lançamento financeiro (livro-razão)."""

    __tablename__ = "financial_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    date: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<FinancialEntryModel(id={self.id!r}, type={self.type!r})>"
