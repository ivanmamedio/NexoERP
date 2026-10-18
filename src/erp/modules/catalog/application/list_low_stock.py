"""List low stock products use case."""

from __future__ import annotations

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product


class ListLowStockOutput:
    def __init__(self, products: list[Product]) -> None:
        self.products = products


class ListLowStock:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(self, *, company_id: int | None = None) -> ListLowStockOutput:
        products = self._repository.list_all(company_id=company_id)
        low = [p for p in products if p.active and p.is_low_stock()]
        return ListLowStockOutput(products=low)
