"""Stock movement domain entity (bookkeeping of inventory changes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class StockMovement(Entity):
    """Um movimento de estoque (entrada ou saída)."""

    product_id: int = 0
    company_id: int | None = None
    quantity_thousandths: int = 0  # positivo = entrada, negativo = saída
    movement_type: str = ""  # "adjustment", "sale", "purchase", "return"
    reference_id: int | None = None  # id da venda/compra/etc quando aplicável
    notes: str = ""
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    user_id: int | None = None
    username: str = ""

    def __post_init__(self) -> None:
        if self.movement_type:
            self.movement_type = self.movement_type.strip().lower()
