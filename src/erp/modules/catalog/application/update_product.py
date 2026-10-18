"""Update product use case."""

from __future__ import annotations

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.domain.errors import NotFound, ValidationError


class UpdateProductInput:
    def __init__(
        self,
        *,
        product_id: int,
        sku: str | None = None,
        name: str | None = None,
        description: str | None = None,
        category_id: int | None = None,
        supplier_id: int | None = None,
        unit: str | None = None,
        cost_cents: int | None = None,
        margin_pct: int | None = None,
        min_stock_qty: int | None = None,
        sold_by_weight: bool | None = None,
        active: bool | None = None,
        company_id: int | None = None,
    ) -> None:
        self.product_id = product_id
        self.sku = sku
        self.name = name
        self.description = description
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.unit = unit
        self.cost_cents = cost_cents
        self.margin_pct = margin_pct
        self.min_stock_qty = min_stock_qty
        self.sold_by_weight = sold_by_weight
        self.active = active
        self.company_id = company_id


class UpdateProductOutput:
    def __init__(self, product: Product) -> None:
        self.product = product


class UpdateProduct:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(self, input: UpdateProductInput) -> UpdateProductOutput:
        product = self._repository.get_by_id(input.product_id)
        if product is None:
            raise NotFound(f"Produto {input.product_id} não encontrado.")
        if product.company_id != input.company_id:
            raise ValidationError("Produto pertence a outra empresa.")

        if input.sku is not None:
            if not input.sku:
                raise ValidationError("SKU não pode ser vazio.")
            product.sku = input.sku.strip().upper()
        if input.name is not None:
            if not input.name:
                raise ValidationError("Nome não pode ser vazio.")
            product.name = input.name.strip()
        if input.description is not None:
            product.description = input.description
        if input.category_id is not None:
            product.category_id = input.category_id
        if input.supplier_id is not None:
            product.supplier_id = input.supplier_id
        if input.unit is not None:
            product.unit = input.unit or "un"
        if input.cost_cents is not None:
            product.cost_cents = input.cost_cents
        if input.margin_pct is not None:
            product.margin_pct = input.margin_pct
        if input.min_stock_qty is not None:
            product.min_stock_qty = input.min_stock_qty
        if input.sold_by_weight is not None:
            product.sold_by_weight = input.sold_by_weight
        if input.active is not None:
            product.active = input.active

        self._repository.save(product)
        return UpdateProductOutput(product=product)
