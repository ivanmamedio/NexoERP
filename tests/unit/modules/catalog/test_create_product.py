"""Unit tests for CreateProduct use case."""

from __future__ import annotations

import pytest

from erp.modules.catalog.application.create_product import (
    CreateProduct,
    CreateProductInput,
)
from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.domain.errors import ValidationError


class FakeProductRepository(ProductRepository):
    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._by_sku: dict[str, Product] = {}
        self._next_id = 1

    def add(self, product: Product) -> None:
        product.id = self._next_id
        self._next_id += 1
        self._products[product.id] = product
        self._by_sku[product.sku] = product

    def save(self, product: Product) -> None:
        self._products[product.id] = product

    def get_by_id(self, product_id: int) -> Product | None:
        return self._products.get(product_id)

    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None:
        return self._by_sku.get(sku)

    def list_all(self, company_id: int | None = None) -> list[Product]:
        return list(self._products.values())

    def delete(self, product_id: int) -> None:
        self._products.pop(product_id, None)


def test_create_product_success() -> None:
    repo = FakeProductRepository()
    uc = CreateProduct(repo)

    output = uc.execute(
        CreateProductInput(
            sku="PROD-001",
            name="Arroz 5kg",
            description="Arroz tipo 1",
            unit="un",
            cost_cents=1000,
            margin_pct=3000,
            price_cents=1300,
            min_stock_qty=10000,
            stock_qty=50000,
            sold_by_weight=False,
            active=True,
            company_id=1,
        )
    )

    assert output.product.id == 1
    assert output.product.sku == "PROD-001"
    assert output.product.name == "Arroz 5kg"
    assert output.product.company_id == 1
    assert output.product.is_low_stock() is False

    stored = repo.get_by_sku("PROD-001")
    assert stored is not None
    assert stored.name == "Arroz 5kg"


def test_create_product_duplicate_sku() -> None:
    repo = FakeProductRepository()
    uc = CreateProduct(repo)

    uc.execute(
        CreateProductInput(
            sku="PROD-001",
            name="Arroz 5kg",
            unit="un",
            cost_cents=1000,
            price_cents=1300,
            company_id=1,
        )
    )

    with pytest.raises(ValidationError, match="Já existe produto com SKU"):
        uc.execute(
            CreateProductInput(
                sku="PROD-001",
                name="Outro Produto",
                unit="un",
                cost_cents=1000,
                price_cents=1300,
                company_id=1,
            )
        )


def test_create_product_empty_sku() -> None:
    repo = FakeProductRepository()
    uc = CreateProduct(repo)

    with pytest.raises(ValidationError, match="SKU é obrigatório"):
        uc.execute(
            CreateProductInput(
                sku="",
                name="Arroz 5kg",
                unit="un",
                cost_cents=1000,
                price_cents=1300,
                company_id=1,
            )
        )
