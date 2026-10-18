"""Sale item domain entity (snapshot of description and price)."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class SaleItem(Entity):
    """Item de venda com snapshot de descrição e preço unitário."""

    sale_id: int = 0
    company_id: int | None = None
    product_id: int | None = None
    # Snapshots (imutáveis após finalizar)
    description: str = ""
    unit_price_cents: int = 0
    quantity_thousandths: int = 0
    line_total_cents: int = 0  # unit_price * qty
    unit: str = "un"
    cancelled: bool = False
    cancel_reason: str = ""

    def __post_init__(self) -> None:
        if self.description:
            self.description = self.description.strip()
        if not self.unit:
            self.unit = "un"

    def compute_line_total(self) -> int:
        """line_total = unit_price * qty (arredondado ao centavo)."""
        return int((self.unit_price_cents * self.quantity_thousandths + 500) // 1000)
