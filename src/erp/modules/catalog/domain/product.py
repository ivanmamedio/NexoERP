"""Product domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity
from erp.shared.domain.value_objects import Money, Quantity


@dataclass(slots=True)
class Product(Entity):
    """Produto do catálogo de uma empresa."""

    sku: str = ""
    name: str = ""
    description: str = ""
    category_id: int | None = None
    supplier_id: int | None = None
    unit: str = "un"  # un, kg, g, l, ml
    cost_cents: int = 0  # custo em centavos
    margin_pct: int = 0  # margem em centesimos (ex: 30% = 3000)
    price_cents: int = 0  # preço de venda em centavos
    min_stock_qty: int = 0  # estoque mínimo em milésimos
    stock_qty: int = 0  # estoque atual em milésimos (cache)
    sold_by_weight: bool = False
    active: bool = True
    company_id: int | None = None

    def __post_init__(self) -> None:
        if self.sku:
            self.sku = self.sku.strip().upper()
        if self.name:
            self.name = self.name.strip()
        if not self.unit:
            self.unit = "un"

    @property
    def cost(self) -> Money:
        return Money(cents=self.cost_cents)

    @property
    def price(self) -> Money:
        return Money(cents=self.price_cents)

    @property
    def stock(self) -> Quantity:
        return Quantity(thousandths=self.stock_qty)

    @property
    def min_stock(self) -> Quantity:
        return Quantity(thousandths=self.min_stock_qty)

    def is_low_stock(self) -> bool:
        return self.stock_qty <= self.min_stock_qty
