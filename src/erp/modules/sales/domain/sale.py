"""Sale domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


class SaleStatus:
    """Sale lifecycle statuses."""

    DRAFT = "draft"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Sale(Entity):
    """Venda com itens, pagamentos e lifecycle."""

    company_id: int | None = None
    session_id: int | None = None  # cash session (PDV)
    user_id: int | None = None
    username: str = ""
    status: str = SaleStatus.DRAFT
    subtotal_cents: int = 0  # soma dos itens (preço x qtd, sem desconto)
    discount_cents: int = 0  # desconto aplicado (centavos)
    total_cents: int = 0  # subtotal - desconto
    paid_cents: int = 0  # soma dos pagamentos
    change_cents: int = 0  # troco = paid - total (quando pago em dinheiro)
    cancel_reason: str = ""
    cancelled_by_user_id: int | None = None
    cancelled_by_username: str = ""
    authorized_by_user_id: int | None = None  # supervisor (desconto/cancelamento via PIN)
    authorized_by_username: str = ""
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    finalized_at: datetime | None = None
    cancelled_at: datetime | None = None

    def is_draft(self) -> bool:
        return self.status == SaleStatus.DRAFT

    def is_finalized(self) -> bool:
        return self.status == SaleStatus.FINALIZED

    def is_cancelled(self) -> bool:
        return self.status == SaleStatus.CANCELLED

    def recalculate(self, items_subtotal_cents: int) -> None:
        """Recalcula subtotal/total a partir do subtotal dos itens."""
        if not self.is_draft():
            raise ValueError("Only draft sales can be recalculated.")
        self.subtotal_cents = items_subtotal_cents
        self.total_cents = max(0, items_subtotal_cents - self.discount_cents)

    def apply_discount(self, discount_cents: int) -> None:
        if not self.is_draft():
            raise ValueError("Only draft sales can receive discounts.")
        if discount_cents < 0:
            raise ValueError("Discount cannot be negative.")
        if discount_cents > self.subtotal_cents:
            raise ValueError("Discount cannot exceed subtotal.")
        self.discount_cents = discount_cents
        self.total_cents = self.subtotal_cents - discount_cents

    def finalize(self, paid_cents: int, change_cents: int) -> None:
        if not self.is_draft():
            raise ValueError("Only draft sales can be finalized.")
        self.paid_cents = paid_cents
        self.change_cents = change_cents
        self.status = SaleStatus.FINALIZED
        self.finalized_at = datetime.now(UTC)

    def cancel(self, *, reason: str, user_id: int | None, username: str) -> None:
        if self.is_cancelled():
            raise ValueError("Sale is already cancelled.")
        if not reason:
            raise ValueError("Cancel reason is required.")
        self.status = SaleStatus.CANCELLED
        self.cancelled_at = datetime.now(UTC)
        self.cancel_reason = reason
        self.cancelled_by_user_id = user_id
        self.cancelled_by_username = username
