"""Unit tests for StartSale and AddItem use cases."""

from __future__ import annotations

import pytest

from erp.modules.catalog.domain.product import Product
from erp.modules.sales.application.add_item import AddItem, AddItemInput
from erp.modules.sales.application.start_sale import StartSale, StartSaleInput
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.shared.domain.errors import NotFound, ValidationError


class FakeSaleRepository:
    def __init__(self) -> None:
        self._sales: dict[int, Sale] = {}
        self._next_id = 1

    def add(self, sale: Sale) -> None:
        sale.id = self._next_id
        self._next_id += 1
        self._sales[sale.id] = sale

    def save(self, sale: Sale) -> None:
        self._sales[sale.id] = sale  # type: ignore[index]

    def get_by_id(self, sale_id: int) -> Sale | None:
        return self._sales.get(sale_id)

    def list_open(self, company_id: int | None = None) -> list[Sale]:
        return [s for s in self._sales.values() if s.is_draft()]


class FakeItemRepository:
    def __init__(self) -> None:
        self._items: dict[int, SaleItem] = {}
        self._next_id = 1

    def add(self, item: SaleItem) -> None:
        item.id = self._next_id
        self._next_id += 1
        self._items[item.id] = item

    def save(self, item: SaleItem) -> None:
        self._items[item.id] = item  # type: ignore[index]

    def get_by_id(self, item_id: int) -> SaleItem | None:
        return self._items.get(item_id)

    def list_by_sale(self, sale_id: int) -> list[SaleItem]:
        return [i for i in self._items.values() if i.sale_id == sale_id]


class FakeProductRepository:
    def __init__(self) -> None:
        self._products: dict[int, Product] = {}

    def add(self, product: Product) -> None:
        assert product.id is not None
        self._products[product.id] = product

    def save(self, product: Product) -> None:
        assert product.id is not None
        self._products[product.id] = product

    def get_by_id(self, product_id: int) -> Product | None:
        return self._products.get(product_id)

    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None:
        for p in self._products.values():
            if p.sku == sku:
                return p
        return None

    def list_all(self, company_id: int | None = None) -> list[Product]:
        return list(self._products.values())

    def delete(self, product_id: int) -> None:
        self._products.pop(product_id, None)


def _make_product() -> Product:
    return Product(
        id=1,
        sku="ARROZ-5KG",
        name="Arroz 5kg",
        unit="un",
        price_cents=2500,
        stock_qty=100000,
        company_id=1,
    )


def test_start_sale() -> None:
    repo = FakeSaleRepository()
    uc = StartSale(repo)
    output = uc.execute(StartSaleInput(user_id=1, username="caixa", company_id=1))
    assert output.sale.id == 1
    assert output.sale.is_draft()


def test_add_item_by_sku() -> None:
    sale_repo = FakeSaleRepository()
    item_repo = FakeItemRepository()
    prod_repo = FakeProductRepository()
    prod_repo.add(_make_product())

    sale = StartSale(sale_repo).execute(
        StartSaleInput(user_id=1, username="caixa", company_id=1)
    ).sale

    output = AddItem(sale_repo, item_repo, prod_repo).execute(
        AddItemInput(sale_id=sale.id or 0, query="ARROZ-5KG", quantity_thousandths=2000)
    )
    assert output.item.description == "Arroz 5kg"
    assert output.item.unit_price_cents == 2500
    assert output.sale_total_cents == 5000


def test_add_item_multiplier() -> None:
    """Multiplicador '3*CODIGO'."""
    sale_repo = FakeSaleRepository()
    item_repo = FakeItemRepository()
    prod_repo = FakeProductRepository()
    prod_repo.add(_make_product())

    sale = StartSale(sale_repo).execute(
        StartSaleInput(user_id=1, username="caixa", company_id=1)
    ).sale

    output = AddItem(sale_repo, item_repo, prod_repo).execute(
        AddItemInput(sale_id=sale.id or 0, query="3*ARROZ-5KG", quantity_thousandths=1000)
    )
    assert output.item.quantity_thousandths == 3000
    assert output.sale_total_cents == 7500


def test_add_item_insufficient_stock() -> None:
    sale_repo = FakeSaleRepository()
    item_repo = FakeItemRepository()
    prod_repo = FakeProductRepository()
    prod_repo.add(_make_product())

    sale = StartSale(sale_repo).execute(
        StartSaleInput(user_id=1, username="caixa", company_id=1)
    ).sale

    with pytest.raises(ValidationError, match="Estoque insuficiente"):
        AddItem(sale_repo, item_repo, prod_repo).execute(
            AddItemInput(
                sale_id=sale.id or 0, query="ARROZ-5KG", quantity_thousandths=200000
            )
        )


def test_add_item_product_not_found() -> None:
    sale_repo = FakeSaleRepository()
    item_repo = FakeItemRepository()
    prod_repo = FakeProductRepository()

    sale = StartSale(sale_repo).execute(
        StartSaleInput(user_id=1, username="caixa", company_id=1)
    ).sale

    with pytest.raises(NotFound, match="não encontrado"):
        AddItem(sale_repo, item_repo, prod_repo).execute(
            AddItemInput(sale_id=sale.id or 0, query="INEXISTENTE")
        )
