"""SQLAlchemy models for the settings module."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime


class SettingModel(Base):
    """Settings table (company-scoped key-value configuration)."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String, nullable=False, default="")
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=datetime.now(UTC), nullable=False
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    __table_args__ = (
        # Uma chave por empresa (evita duplicatas)
        None,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SettingModel(id={self.id!r}, company_id={self.company_id}, key={self.key!r})>"
