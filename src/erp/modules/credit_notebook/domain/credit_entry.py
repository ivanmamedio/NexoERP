"""Credit entry domain entity (individual credit transaction)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from erp.shared.domain.entities import Entity
from erp.shared.domain.value_objects import Money

if TYPE_CHECKING:
    from erp.modules.credit_notebook.domain.credit_customer import CreditCustomer


class CreditEntryType(StrEnum):
    """Tipo de lançamento no caderno de fiado."""

    CHARGE = "charge"  # Venda a prazo (aumenta dívida)
    PAYMENT = "payment"  # Pagamento/abatimento (diminui dívida)
    ADJUSTMENT = "adjustment"  # Ajuste manual (pode ser + ou -)
    INTEREST = "interest"  # Juros/mora


class CreditEntryStatus(StrEnum):
    """Status do lançamento."""

    PENDING = "pending"  # Pendente (para pagamentos futuros)
    PAID = "paid"  # Pago/quitado
    PARTIAL = "partial"  # Parcialmente pago
    CANCELLED = "cancelled"  # Cancelado


@dataclass(slots=True)
class CreditEntry(Entity):
    """Lançamento individual no caderno de fiado."""

    customer_id: int = 0
    company_id: int | None = None
    entry_type: str = CreditEntryType.CHARGE
    description: str = ""
    amount_cents: int = 0  # Valor do lançamento (sempre positivo)
    status: str = CreditEntryStatus.PENDING
    due_date: datetime | None = None
    paid_at: datetime | None = None
    paid_amount_cents: int = 0
    reference_type: str = ""  # "sale", "manual", etc.
    reference_id: int | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: int | None = None
    created_by_username: str = ""

    # Transient
    _customer: CreditCustomer | None = field(default=None, repr=False)

    @property
    def amount(self) -> Money:
        return Money(self.amount_cents)

    @property
    def paid_amount(self) -> Money:
        return Money(self.paid_amount_cents)

    @property
    def pending_amount_cents(self) -> int:
        return max(0, self.amount_cents - self.paid_amount_cents)

    @property
    def pending_amount(self) -> Money:
        return Money(self.pending_amount_cents)

    def is_charge(self) -> bool:
        return self.entry_type == CreditEntryType.CHARGE

    def is_payment(self) -> bool:
        return self.entry_type == CreditEntryType.PAYMENT

    def apply_payment(self, amount_cents: int, paid_at: datetime | None = None) -> bool:
        """Aplica um pagamento a este lançamento.
        
        Returns True se o lançamento foi totalmente quitado.
        """
        if self.status == CreditEntryStatus.PAID:
            return False

        if amount_cents <= 0:
            raise ValueError("Valor do pagamento deve ser positivo")

        if amount_cents > self.pending_amount_cents:
            raise ValueError("Valor excede o pendente")

        self.paid_amount_cents += amount_cents
        if paid_at is not None:
            self.paid_at = paid_at

        if self.paid_amount_cents >= self.amount_cents:
            self.status = CreditEntryStatus.PAID
            self.paid_at = paid_at or datetime.now(UTC)
        elif self.paid_amount_cents > 0:
            self.status = CreditEntryStatus.PARTIAL

        return self.status == CreditEntryStatus.PAID

    def cancel(self) -> None:
        """Cancela o lançamento."""
        if self.status == CreditEntryStatus.PAID:
            raise ValueError("Não é possível cancelar lançamento já quitado")
        self.status = CreditEntryStatus.CANCELLED

    def __post_init__(self) -> None:
        if self.description:
            self.description = self.description.strip()
        if self.notes:
            self.notes = self.notes.strip()
        if self.reference_type:
            self.reference_type = self.reference_type.strip()
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=UTC)
        if self.due_date is not None and self.due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=UTC)
        if self.paid_at is not None and self.paid_at.tzinfo is None:
            self.paid_at = self.paid_at.replace(tzinfo=UTC)