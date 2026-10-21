"""Payable domain entity with installments and recurrence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from erp.shared.domain.entities import Entity
from erp.shared.domain.value_objects import Money


class PayableStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"


class RecurrenceType(StrEnum):
    NONE = "none"
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"
    WEEKLY = "weekly"


@dataclass(slots=True)
class PayableInstallment(Entity):
    """Parcela de uma conta a pagar."""

    payable_id: int = 0
    installment_number: int = 1
    due_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    amount_cents: int = 0
    status: str = field(default=PayableStatus.PENDING)
    paid_at: datetime | None = None
    paid_amount_cents: int = 0

    @property
    def amount(self) -> Money:
        return Money(self.amount_cents)

    @property
    def paid_amount(self) -> Money:
        return Money(self.paid_amount_cents)

    @property
    def pending_amount(self) -> Money:
        return Money(max(0, self.amount_cents - self.paid_amount_cents))

    def pay(self, amount_cents: int, paid_at: datetime | None = None) -> None:
        """Registra pagamento na parcela."""
        if self.status == PayableStatus.PAID:
            raise ValueError("Parcela já quitada")
        if amount_cents <= 0:
            raise ValueError("Valor do pagamento deve ser positivo")

        self.paid_amount_cents += amount_cents
        if paid_at is not None:
            self.paid_at = paid_at

        if self.paid_amount_cents >= self.amount_cents:
            self.status = PayableStatus.PAID
            self.paid_at = paid_at or datetime.now(UTC)
        elif self.paid_amount_cents > 0:
            self.status = PayableStatus.PARTIAL

    def __post_init__(self) -> None:
        if self.due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=UTC)


@dataclass
class Payable(Entity):
    """Conta a pagar com suporte a parcelamento e recorrência."""

    company_id: int | None = None
    supplier_id: int | None = None
    category_id: int | None = None
    description: str = ""
    total_amount_cents: int = 0
    status: str = field(default=PayableStatus.PENDING)
    issue_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    recurrence_type: str = field(default="none")  # none, monthly, biweekly, weekly
    recurrence_count: int = 1  # total de parcelas (para recorrência)
    installments: list[PayableInstallment] = field(default_factory=list)
    source_type: str = ""  # "purchase", "expense", etc.
    source_id: int | None = None

    @property
    def total_amount(self) -> Money:
        return Money(self.total_amount_cents)

    @property
    def paid_amount_cents(self) -> int:
        return sum(inst.paid_amount_cents for inst in self.installments)

    @property
    def paid_amount(self) -> Money:
        return Money(self.paid_amount_cents)

    @property
    def pending_amount_cents(self) -> int:
        return sum(inst.pending_amount.cents for inst in self.installments)

    @property
    def pending_amount(self) -> Money:
        return Money(self.pending_amount_cents)

    def add_installment(
        self,
        installment_number: int,
        due_date: datetime,
        amount_cents: int,
    ) -> PayableInstallment:
        """Adiciona uma parcela à conta a pagar."""
        installment = PayableInstallment(
            installment_number=installment_number,
            due_date=due_date,
            amount_cents=amount_cents,
            status=PayableStatus.PENDING,
        )
        self.installments.append(installment)
        return installment

    def create_installments(
        self,
        first_due_date: datetime,
        interval_days: int = 30,
    ) -> list[PayableInstallment]:
        """Cria parcelas iguais a partir da data inicial."""
        if self.recurrence_count <= 1:
            return []

        amount_per_installment = self.total_amount_cents // self.recurrence_count
        remainder = self.total_amount_cents % self.recurrence_count

        installments = []
        current_date = first_due_date

        for i in range(1, self.recurrence_count + 1):
            amount = amount_per_installment + (1 if i <= remainder else 0)
            installment = self.add_installment(i, current_date, amount)
            installments.append(installment)
            current_date = self._add_days(current_date, interval_days)

        return installments

    @staticmethod
    def _add_days(date: datetime, days: int) -> datetime:
        """Adiciona dias a uma data, mantendo timezone."""
        from datetime import timedelta

        return date.replace(tzinfo=None) + timedelta(days=days)

    def pay_installment(
        self,
        installment_number: int,
        amount_cents: int,
        paid_at: datetime | None = None,
    ) -> None:
        """Registra pagamento de uma parcela específica."""
        installment = next(
            (i for i in self.installments if i.installment_number == installment_number),
            None,
        )
        if installment is None:
            raise ValueError(f"Parcela {installment_number} não encontrada")
        installment.pay(amount_cents, paid_at)
        self._update_status()

    def _update_status(self) -> None:
        """Atualiza status geral baseado nas parcelas."""
        if not self.installments:
            self.status = PayableStatus.PENDING
            return

        all_paid = all(i.status == PayableStatus.PAID for i in self.installments)
        any_paid = any(i.status != PayableStatus.PENDING for i in self.installments)

        if all_paid:
            self.status = PayableStatus.PAID
        elif any_paid:
            self.status = PayableStatus.PARTIAL
        else:
            self.status = PayableStatus.PENDING

    def cancel(self) -> None:
        """Cancela a conta a pagar e todas as parcelas pendentes."""
        self.status = PayableStatus.CANCELLED
        for inst in self.installments:
            if inst.status == PayableStatus.PENDING:
                inst.status = PayableStatus.CANCELLED

    def __post_init__(self) -> None:
        if self.issue_date.tzinfo is None:
            self.issue_date = self.issue_date.replace(tzinfo=UTC)
