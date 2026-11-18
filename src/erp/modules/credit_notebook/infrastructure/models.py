"""SQLAlchemy models for the credit notebook module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.shared.infrastructure.database import Base, TimestampMixin
from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class CreditCustomerModel(Base, TimestampMixin):
    """Cliente do caderno de fiado."""

    __tablename__ = "credit_customers"
    __table_args__ = (
        Index("ix_credit_customers_company_phone", "company_id", "phone"),
        Index("ix_credit_customers_company_name", "company_id", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    credit_limit_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)

    entries: Mapped[list["CreditEntryModel"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CreditCustomerModel(id={self.id!r}, name={self.name!r})>"


class CreditEntryModel(Base, TimestampMixin):
    """Lançamento do caderno de fiado."""

    __tablename__ = "credit_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("credit_customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False, default="charge", index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    due_date: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    paid_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)

    customer: Mapped["CreditCustomerModel"] = relationship(back_populates="entries")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CreditEntryModel(id={self.id!r}, customer_id={self.customer_id}, type={self.entry_type!r})>"