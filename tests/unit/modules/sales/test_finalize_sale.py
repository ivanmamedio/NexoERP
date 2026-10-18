"""Unit tests for FinalizeSale use case (payment, change, atomicity)."""

from __future__ import annotations

import pytest

from erp.modules.catalog.domain.product import Product
from erp.modules.sales.application.finalize_sale import (
    FinalizePaymentInput,
    FinalizeSale,
    FinalizeSaleInput,
)
from erp.modules.sales.application.start_sale import StartSale, StartSaleInput
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.shared.application.events import EventBus
from erp.shared.domain.errors import ValidationError


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


class FakePaymentRepository:
    def __init__(self) -> None:
        self._payments: list = []

    def add(self, payment) -> None:  # type: ignore[no-untyped-def]
        self._payments.append(payment)

    def list_by_sale(self, sale_id: int) -> list:
        return [p for p in self._payments if p.sale_id == sale_id]


class FakeProductRepository:
    def __init__(self, stock_qty: int = 100000) -> None:
        self._products: dict[int, Product] = {
            1: Product(
                id=1,
                sku="ARROZ-5KG",
                name="Arroz 5kg",
                unit="un",
                price_cents=2500,
                stock_qty=stock_qty,
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


def _make_setup(*, stock_qty: int = 100000) -> tuple:
    sale_repo = FakeSaleRepository()
    item_repo = FakeItemRepository()
    payment_repo = FakePaymentRepository()
    prod_repo = FakeProductRepository(stock_qty=stock_qty)
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
    return sale_repo, item_repo, payment_repo, prod_repo, sale


def test_finalize_cash_exact() -> None:
    sale_repo, item_repo, payment_repo, prod_repo, sale = _make_setup()

    uc = FinalizeSale(sale_repo, item_repo, payment_repo, prod_repo, EventBus())
    output = uc.execute(
        FinalizeSaleInput(
            sale_id=sale.id or 0,
            payments=[FinalizePaymentInput(method="cash", amount_cents=5000)],
            user_id=1,
            username="caixa",
            session_id=1,
            company_id=1,
        )
    )
    assert output.change_cents == 0
    assert output.sale.is_finalized()
    assert prod_repo.get_by_id(1).stock_qty == 98000


def test_finalize_with_change() -> None:
    sale_repo, item_repo, payment_repo, prod_repo, sale = _make_setup()

    uc = FinalizeSale(sale_repo, item_repo, payment_repo, prod_repo, EventBus())
    output = uc.execute(
        FinalizeSaleInput(
            sale_id=sale.id or 0,
            payments=[FinalizePaymentInput(method="cash", amount_cents=10000)],
            user_id=1,
            username="caixa",
            company_id=1,
        )
    )
    assert output.change_cents == 5000


def test_finalize_mixed_payment() -> None:
    sale_repo, item_repo, payment_repo, prod_repo, sale = _make_setup()

    uc = FinalizeSale(sale_repo, item_repo, payment_repo, prod_repo, EventBus())
    output = uc.execute(
        FinalizeSaleInput(
            sale_id=sale.id or 0,
            payments=[
                FinalizePaymentInput(method="cash", amount_cents=3000),
                FinalizePaymentInput(method="pix", amount_cents=2000),
            ],
            user_id=1,
            username="caixa",
            company_id=1,
        )
    )
    assert output.change_cents == 0
    payments = payment_repo.list_by_sale(sale.id or 0)
    assert len(payments) == 2


def test_finalize_insufficient_payment() -> None:
    sale_repo, item_repo, payment_repo, prod_repo, sale = _make_setup()

    uc = FinalizeSale(sale_repo, item_repo, payment_repo, prod_repo, EventBus())
    with pytest.raises(ValidationError, match="insuficiente"):
        uc.execute(
            FinalizeSaleInput(
                sale_id=sale.id or 0,
                payments=[FinalizePaymentInput(method="cash", amount_cents=1000)],
                user_id=1,
                username="caixa",
                company_id=1,
            )
        )


def test_finalize_stock_failure_is_atomic() -> None:
    """Estoque insuficiente no fechamento -> a venda continua em rascunho."""
    sale_repo, item_repo, payment_repo, prod_repo, sale = _make_setup(stock_qty=1000)

    uc = FinalizeSale(sale_repo, item_repo, payment_repo, prod_repo, EventBus())
    with pytest.raises(ValidationError, match="Estoque insuficiente"):
        uc.execute(
            FinalizeSaleInput(
                sale_id=sale.id or 0,
                payments=[FinalizePaymentInput(method="cash", amount_cents=5000)],
                user_id=1,
                username="caixa",
                company_id=1,
            )
        )
    assert sale_repo.get_by_id(sale.id or 0).is_draft()
