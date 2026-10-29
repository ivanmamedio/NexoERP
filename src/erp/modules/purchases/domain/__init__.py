"""Purchases domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Purchase(Entity):
    """Entrada de mercadoria (compra de produtos)."""

    company_id: int = 0
    supplier_id: int | None = None
    user_id: int | None = None
    username: str = ""
    purchase_date: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    total_cents: int = 0
    status: str = "registered"  # registered, cancelled

    def is_registered(self) -> bool:
        return self.status == "registered"

    def is_cancelled(self) -> bool:
        return self.status == "cancelled"


@dataclass(slots=True)
class PurchaseItem(Entity):
    """Item de uma compra (mercadoria entrada)."""

    purchase_id: int = 0
    product_id: int | None = None
    quantity_thousandths: int = 0
    unit_cost_cents: int = 0
    line_total_cents: int = 0
