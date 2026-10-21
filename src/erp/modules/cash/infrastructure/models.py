"""SQLAlchemy models for the cash module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base, TimestampMixin
from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class CashRegisterModel(Base, TimestampMixin):
    """Cash register (terminal) table."""

    __tablename__ = "cash_registers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    terminal_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CashRegisterModel(id={self.id!r}, terminal={self.terminal_code!r})>"


class CashSessionModel(Base, TimestampMixin):
    """Cash session table."""

    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    register_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    opened_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opened_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    opened_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    opening_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    closed_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closed_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    closing_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    total_sales_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_suprimentos_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_sangrias_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_pix_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_card_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_cash_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difference_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    closed: Mapped[bool] = mapped_column(default=False, nullable=False)
    blind_close: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CashSessionModel(id={self.id!r}, register_id={self.register_id!r})>"


class CashMovementModel(Base):
    """Cash movement table."""

    __tablename__ = "cash_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CashMovementModel(id={self.id!r}, session_id={self.session_id!r})>"
