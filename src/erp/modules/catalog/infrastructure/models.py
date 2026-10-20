"""SQLAlchemy models for the catalog module."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base
from erp.shared.infrastructure.database.types import UTCDateTime


def _utcnow() -> datetime:
    """Evaluated on every INSERT/UPDATE (never once at import time)."""
    return datetime.now(UTC)


class CategoryModel(Base):
    """Category table."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CategoryModel(id={self.id!r}, name={self.name!r})>"


class SupplierModel(Base):
    """Supplier table."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    trade_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SupplierModel(id={self.id!r}, name={self.name!r})>"


class ProductModel(Base):
    """Product table."""

    __tablename__ = "products"
    __table_args__ = (
        # Composite indexes used by the PDV: prefix name search and barcode/SKU
        # lookup are always scoped by company_id.
        Index(
            "ix_products_company_name_nocase",
            "company_id",
            text("name COLLATE NOCASE"),
        ),
        Index("ix_products_company_sku", "company_id", "sku"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit: Mapped[str] = mapped_column(String(10), nullable=False, default="un")
    cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    margin_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sold_by_weight: Mapped[bool] = mapped_column(default=False, nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ProductModel(id={self.id!r}, sku={self.sku!r})>"


class StockMovementModel(Base):
    """Stock movement table (audit trail of inventory changes)."""

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    quantity_thousandths: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<StockMovementModel(id={self.id!r}, product_id={self.product_id!r})>"


class PriceHistoryModel(Base):
    """Price history table (audit trail of price changes)."""

    __tablename__ = "price_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    old_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    new_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    changed_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    changed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PriceHistoryModel(id={self.id!r}, product_id={self.product_id!r})>"
