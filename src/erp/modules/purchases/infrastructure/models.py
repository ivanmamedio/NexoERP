"""SQLAlchemy models for the purchases module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base, TimestampMixin
from erp.shared.infrastructure.database.types import UTCDateTime


class PurchaseModel(Base, TimestampMixin):
    """Purchase table (entrada de mercadoria)."""

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    purchase_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="registered")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PurchaseModel(id={self.id!r}, total={self.total_cents})>"


class PurchaseItemModel(Base, TimestampMixin):
    """Purchase item table (itens de uma compra)."""

    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity_thousandths: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PurchaseItemModel(id={self.id!r}, purchase_id={self.purchase_id})>"
