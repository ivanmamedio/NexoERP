"""SearchProducts query — sugestões de produto para o PDV (busca por nome)."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.catalog.application.ports import ProductRepository


@dataclass(slots=True, frozen=True)
class ProductSearchItem:
    """Resultado resumido de busca de produto (sem expor o domain do catalog)."""

    product_id: int
    sku: str
    name: str
    price_cents: int
    stock_qty: int
    unit: str


class SearchProducts:
    """Busca produtos ativos por nome, limitada por empresa."""

    def __init__(self, product_repo: ProductRepository) -> None:
        self._product_repo = product_repo

    def execute(
        self, *, query: str, company_id: int | None = None, limit: int = 10
    ) -> list[ProductSearchItem]:
        products = self._product_repo.search(query, company_id, limit)
        return [
            ProductSearchItem(
                product_id=product.id or 0,
                sku=product.sku,
                name=product.name,
                price_cents=product.price_cents,
                stock_qty=product.stock_qty,
                unit=product.unit,
            )
            for product in products
        ]
