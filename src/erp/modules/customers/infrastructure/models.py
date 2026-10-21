"""SQLAlchemy models for the customers module."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.shared.infrastructure.database import Base, TimestampMixin


class CustomerModel(Base, TimestampMixin):
    """Customer table (cadastro de clientes, dados mínimos LGPD)."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    document: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    credit_limit_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<CustomerModel(id={self.id!r}, name={self.name!r})>"
