"""Unit tests for AdjustStock use case."""

from __future__ import annotations

import pytest

from erp.modules.catalog.application.adjust_stock import (
    AdjustStock,
    AdjustStockInput,
)
from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.domain.errors import NotFound, ValidationError


class FakeProductRepository(ProductRepository):
    def __init__(self) -> None:
        self._products: dict[int, Product] = {}

    def add(self, product: Product) -> None:
        self._products[product.id] = product

    def save(self, product: Product) -> None:
        self._products[product.id] = product

    def get_by_id(self, product_id: int) -> Product | None:
        return self._products.get(product_id)

    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None:
        return None

    def list_all(self, company_id: int | None = None) -> list[Product]:
        return list(self._products.values())

    def delete(self, product_id: int) -> None:
        self._products.pop(product_id, None)


def test_adjust_stock_increases() -> None:
    repo = FakeProductRepository()
    product = Product(id=1, sku="P001", name="Produto", unit="un", stock_qty=10000, company_id=1)
    repo.add(product)

    uc = AdjustStock(repo)
    output = uc.execute(
        AdjustStockInput(
            product_id=1,
            quantity_thousandths=50000,
            movement_type="purchase",
            user_id=1,
            username="admin",
            company_id=1,
        )
    )

    assert output.new_stock_qty == 60000
    assert repo.get_by_id(1).stock_qty == 60000


def test_adjust_stock_cannot_go_negative() -> None:
    repo = FakeProductRepository()
    product = Product(id=1, sku="P001", name="Produto", unit="un", stock_qty=10000, company_id=1)
    repo.add(product)

    uc = AdjustStock(repo)
    with pytest.raises(ValidationError, match="estoque negativo"):
        uc.execute(
            AdjustStockInput(
                product_id=1,
                quantity_thousandths=-50000,
                movement_type="adjustment",
                company_id=1,
            )
        )


def test_adjust_stock_not_found() -> None:
    repo = FakeProductRepository()
    uc = AdjustStock(repo)
    with pytest.raises(NotFound):
        uc.execute(
            AdjustStockInput(
                product_id=999,
                quantity_thousandths=1000,
                company_id=1,
            )
        )
