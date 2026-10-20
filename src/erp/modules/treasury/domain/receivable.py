"""Receivable domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from erp.shared.domain.entities import Entity
from erp.shared.domain.value_objects import Money


class ReceivableStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Receivable(Entity):
    """Conta a receber."""

    company_id: int | None = None
    customer_id: int | None = None
    category_id: int | None = None
    description: str = ""
    total_amount_cents: int = 0
    status: str = field(default=ReceivableStatus.PENDING)
    issue_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    due_date: datetime | None = None
    received_at: datetime | None = None
    received_amount_cents: int = 0
    source_type: str = ""  # "sale", "service", etc.
    source_id: int | None = None

    @property
    def total_amount(self) -> Money:
        return Money(self.total_amount_cents)

    @property
    def received_amount(self) -> Money:
        return Money(self.received_amount_cents)

    @property
    def pending_amount_cents(self) -> int:
        return max(0, self.total_amount_cents - self.received_amount_cents)

    @property
    def pending_amount(self) -> Money:
        return Money(self.pending_amount_cents)

    def receive(self, amount_cents: int, received_at: datetime | None = None) -> None:
        """Registra recebimento (parcial ou total)."""
        if self.status == ReceivableStatus.RECEIVED:
            raise ValueError("Conta a receber já quitada")
        if amount_cents <= 0:
            raise ValueError("Valor do recebimento deve ser positivo")

        self.received_amount_cents += amount_cents
        if received_at is not None:
            self.received_at = received_at

        if self.received_amount_cents >= self.total_amount_cents:
            self.status = ReceivableStatus.RECEIVED
            self.received_at = received_at or __import__("datetime").datetime.now(
                __import__("datetime").UTC
            )
        elif self.received_amount_cents > 0:
            self.status = ReceivableStatus.PARTIAL

    def cancel(self) -> None:
        """Cancela a conta a receber."""
        self.status = ReceivableStatus.CANCELLED

    def __post_init__(self) -> None:
        if self.issue_date.tzinfo is None:
            self.issue_date = self.issue_date.replace(tzinfo=__import__("datetime").UTC)
        if self.due_date is not None and self.due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=__import__("datetime").UTC)