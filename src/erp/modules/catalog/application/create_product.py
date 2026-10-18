"""Create product use case."""

from __future__ import annotations

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.domain.errors import ValidationError


class CreateProductInput:
    def __init__(
        self,
        *,
        sku: str,
        name: str,
        description: str = "",
        category_id: int | None = None,
        supplier_id: int | None = None,
        unit: str = "un",
        cost_cents: int = 0,
        margin_pct: int = 0,
        price_cents: int = 0,
        min_stock_qty: int = 0,
        stock_qty: int = 0,
        sold_by_weight: bool = False,
        active: bool = True,
        company_id: int | None = None,
    ) -> None:
        self.sku = sku
        self.name = name
        self.description = description
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.unit = unit
        self.cost_cents = cost_cents
        self.margin_pct = margin_pct
        self.price_cents = price_cents
        self.min_stock_qty = min_stock_qty
        self.stock_qty = stock_qty
        self.sold_by_weight = sold_by_weight
        self.active = active
        self.company_id = company_id


class CreateProductOutput:
    def __init__(self, product: Product) -> None:
        self.product = product


class CreateProduct:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(self, input: CreateProductInput) -> CreateProductOutput:
        if not input.sku:
            raise ValidationError("SKU é obrigatório.")
        if not input.name:
            raise ValidationError("Nome do produto é obrigatório.")

        existing = self._repository.get_by_sku(input.sku, input.company_id)
        if existing is not None:
            raise ValidationError(f"Já existe produto com SKU {input.sku} nesta empresa.")

        product = Product(
            sku=input.sku,
            name=input.name,
            description=input.description,
            category_id=input.category_id,
            supplier_id=input.supplier_id,
            unit=input.unit,
            cost_cents=input.cost_cents,
            margin_pct=input.margin_pct,
            price_cents=input.price_cents,
            min_stock_qty=input.min_stock_qty,
            stock_qty=input.stock_qty,
            sold_by_weight=input.sold_by_weight,
            active=input.active,
            company_id=input.company_id,
        )
        self._repository.add(product)
        return CreateProductOutput(product=product)
