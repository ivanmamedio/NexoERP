"""Unit tests for ApplyDiscount and CancelSale/CancelItem use cases."""

from __future__ import annotations

import pytest

from erp.modules.catalog.domain.product import Product
from erp.modules.sales.application.apply_discount import ApplyDiscount, ApplyDiscountInput
from erp.modules.sales.application.cancel_sale import (
    CancelItem,
    CancelItemInput,
    CancelSale,
    CancelSaleInput,
)
from erp.modules.sales.application.start_sale import StartSale, StartSaleInput
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.shared.domain.errors import PermissionDenied


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
        self._products: dict[int, Product] = {
            1: Product(
                id=1,
                sku="ARROZ-5KG",
                name="Arroz 5kg",
                unit="un",
                price_cents=2500,
                stock_qty=100000,
                company_id=1,
            )
        }

    def save(self, product: Product) -> None:
        assert product.id is not None
        self._products[product.id] = product

    def get_by_id(self, product_id: int) -> Product | None:
        return self._products.get(product_id)

    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None:
        return None

    def list_all(self, company_id: int | None = None) -> list[Product]:
        return list(self._products.values())

    def add(self, product: Product) -> None:
        assert product.id is not None
        self._products[product.id] = product

    def delete(self, product_id: int) -> None:
        self._products.pop(product_id, None)


def _make_setup() -> tuple:
    sale_repo = FakeSaleRepository()
    item_repo = FakeItemRepository()
    prod_repo = FakeProductRepository()
    sale = StartSale(sale_repo).execute(
        StartSaleInput(user_id=1, username="caixa", company_id=1)
    ).sale
    item = SaleItem(
        sale_id=sale.id or 0,
        company_id=1,
        product_id=1,
        description="Arroz 5kg",
        unit_price_cents=2500,
        quantity_thousandths=2000,
        unit="un",
    )
    item.line_total_cents = item.compute_line_total()
    item_repo.add(item)
    sale.recalculate(5000)
    sale_repo.save(sale)
    return sale_repo, item_repo, prod_repo, sale


def test_apply_discount_with_permission() -> None:
    sale_repo, _, _, sale = _make_setup()
    output = ApplyDiscount(sale_repo, {"sale.discount"}).execute(
        ApplyDiscountInput(
            sale_id=sale.id or 0, discount_cents=500, user_id=1, username="gerente"
        )
    )
    assert output.new_total_cents == 4500


def test_discount_requires_permission_or_supervisor() -> None:
    sale_repo, _, _, sale = _make_setup()

    with pytest.raises(PermissionDenied, match="sale.discount"):
        ApplyDiscount(sale_repo, set()).execute(
            ApplyDiscountInput(
                sale_id=sale.id or 0, discount_cents=500, user_id=1, username="caixa"
            )
        )

    output = ApplyDiscount(sale_repo, set()).execute(
        ApplyDiscountInput(
            sale_id=sale.id or 0,
            discount_cents=500,
            user_id=1,
            username="caixa",
            supervisor_user_id=2,
            supervisor_username="gerente",
        )
    )
    assert output.new_total_cents == 4500
    assert sale.authorized_by_user_id == 2


def test_cancel_sale_restores_stock() -> None:
    sale_repo, item_repo, prod_repo, sale = _make_setup()
    sale.finalize(paid_cents=5000, change_cents=0)
    sale_repo.save(sale)
    product = prod_repo.get_by_id(1)
    assert product is not None
    product.stock_qty = 98000
    prod_repo.save(product)

    CancelSale(sale_repo, item_repo, prod_repo, {"sale.cancel"}).execute(
        CancelSaleInput(
            sale_id=sale.id or 0, reason="cliente desistiu", user_id=1, username="gerente"
        )
    )
    after = sale_repo.get_by_id(sale.id or 0)
    assert after is not None
    assert after.is_cancelled()
    product_after = prod_repo.get_by_id(1)
    assert product_after is not None
    assert product_after.stock_qty == 100000


def test_cancel_sale_requires_permission() -> None:
    sale_repo, item_repo, prod_repo, sale = _make_setup()
    with pytest.raises(PermissionDenied, match="sale.cancel"):
        CancelSale(sale_repo, item_repo, prod_repo, set()).execute(
            CancelSaleInput(sale_id=sale.id or 0, reason="x", user_id=1, username="caixa")
        )


def test_cancel_item_draft() -> None:
    sale_repo, item_repo, _, sale = _make_setup()
    item = item_repo.list_by_sale(sale.id or 0)[0]
    CancelItem(sale_repo, item_repo, {"sale.cancel"}).execute(
        CancelItemInput(item_id=item.id or 0, reason="erro", user_id=1, username="caixa")
    )
    updated = sale_repo.get_by_id(sale.id or 0)
    assert updated is not None
    assert updated.total_cents == 0

