"""SQLAlchemy models for the treasury module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.shared.infrastructure.database import Base, TimestampMixin
from erp.shared.infrastructure.database.types import UTCDateTime, _utcnow


class FinancialEntryModel(Base):
    """Lançamento financeiro (livro-razão)."""

    __tablename__ = "financial_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    date: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<FinancialEntryModel(id={self.id!r}, type={self.type!r})>"


class FinancialCategoryModel(Base, TimestampMixin):
    """Categoria financeira."""

    __tablename__ = "financial_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # expense, income, transfer
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<FinancialCategoryModel(id={self.id!r}, name={self.name!r})>"


class PayableModel(Base, TimestampMixin):
    """Conta a pagar."""

    __tablename__ = "payables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    issue_date: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    recurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    installments: Mapped[list[PayableInstallmentModel]] = relationship(
        back_populates="payable", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PayableModel(id={self.id!r}, total={self.total_amount_cents})>"


class PayableInstallmentModel(Base):
    """Parcela de conta a pagar."""

    __tablename__ = "payable_installments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payable_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    paid_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    payable: Mapped[PayableModel] = relationship(back_populates="installments")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<PayableInstallmentModel(id={self.id!r}, "
            f"payable_id={self.payable_id}, due={self.due_date})>"
        )


class ReceivableModel(Base, TimestampMixin):
    """Conta a receber."""

    __tablename__ = "receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    issue_date: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    received_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ReceivableModel(id={self.id!r}, total={self.total_amount_cents})>"
