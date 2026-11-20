"""Credit customer domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from erp.shared.domain.entities import Entity
from erp.shared.domain.value_objects import Money

if TYPE_CHECKING:
    from erp.modules.credit_notebook.domain.credit_entry import CreditEntry


@dataclass(slots=True)
class CreditCustomer(Entity):
    """Cliente do caderno de fiado."""

    company_id: int | None = None
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""
    credit_limit_cents: int = 0  # limite de crédito (0 = sem limite)
    status: str = "active"  # active, blocked, inactive
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Transient - populated when needed
    _entries: list[CreditEntry] | None = field(default=None, repr=False)

    @property
    def credit_limit(self) -> Money:
        return Money(self.credit_limit_cents)

    @property
    def current_balance_cents(self) -> int:
        """Saldo devedor atual (soma de todas as entradas não pagas)."""
        if self._entries is None:
            return 0
        return sum(e.pending_amount_cents for e in self._entries if e.status != "paid")

    @property
    def current_balance(self) -> Money:
        return Money(self.current_balance_cents)

    @property
    def available_credit_cents(self) -> int:
        """Crédito disponível (limite - saldo devedor). Se limite for 0, retorna valor alto."""
        if self.credit_limit_cents <= 0:
            return 999999999  # virtually unlimited
        return max(0, self.credit_limit_cents - self.current_balance_cents)

    @property
    def available_credit(self) -> Money:
        return Money(self.available_credit_cents)

    @property
    def is_over_limit(self) -> bool:
        return self.credit_limit_cents > 0 and self.current_balance_cents > self.credit_limit_cents

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked" or self.is_over_limit

    def set_entries(self, entries: list[CreditEntry]) -> None:
        self._entries = entries

    def __post_init__(self) -> None:
        if self.name:
            self.name = self.name.strip()
        if self.phone:
            self.phone = self.phone.strip()
        if self.email:
            self.email = self.email.strip().lower()
        if self.address:
            self.address = self.address.strip()
        if self.notes:
            self.notes = self.notes.strip()
        if self.updated_at.tzinfo is None:
            self.updated_at = self.updated_at.replace(tzinfo=UTC)
