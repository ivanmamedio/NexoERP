"""SQLAlchemy models for the sales module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class SaleModel(Base):
    """Sale table."""

    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paid_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    change_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancel_reason: Mapped[str] = mapped_column(String, nullable=False, default="")
    cancelled_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cancelled_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    authorized_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authorized_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SaleModel(id={self.id!r}, status={self.status!r})>"


class SaleItemModel(Base):
    """Sale item table (snapshot of description and price)."""

    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_thousandths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(10), nullable=False, default="un")
    cancelled: Mapped[bool] = mapped_column(default=False, nullable=False)
    cancel_reason: Mapped[str] = mapped_column(String, nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SaleItemModel(id={self.id!r}, sale_id={self.sale_id!r})>"


class SalePaymentModel(Base):
    """Sale payment table (mixed payments and change)."""

    __tablename__ = "sale_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    change_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SalePaymentModel(id={self.id!r}, sale_id={self.sale_id!r})>"
