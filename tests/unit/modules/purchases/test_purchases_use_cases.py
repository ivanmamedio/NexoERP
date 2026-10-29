"""Unit tests for RegisterPurchase and CountInventory use cases."""

from __future__ import annotations

import re

import pytest

from erp.modules.purchases.application.count_inventory import (
    CountInventory,
    InventoryCountInput,
)
from erp.modules.purchases.application.register_purchase import (
    PurchaseItemInput,
    RegisterPurchase,
    RegisterPurchaseInput,
)
from erp.shared.domain.errors import PermissionDenied, ValidationError


class FakePurchaseRepository:
    def __init__(self) -> None:
        self._purchases: dict[int, object] = {}
        self._next_id = 1

    def add(self, purchase: object) -> None:
        purchase.id = self._next_id
        self._next_id += 1
        self._purchases[purchase.id] = purchase

    def save(self, purchase: object) -> None:
        self._purchases[purchase.id] = purchase

    def get_by_id(self, purchase_id: int) -> object | None:
        return self._purchases.get(purchase_id)

    def list_by_company(self, company_id: int) -> list[object]:
        return [p for p in self._purchases.values() if p.company_id == company_id]


class FakePurchaseItemRepository:
    def __init__(self) -> None:
        self._items: dict[int, object] = {}
        self._next_id = 1

    def add(self, item: object) -> None:
        item.id = self._next_id
        self._next_id += 1
        self._items[item.id] = item

    def save(self, item: object) -> None:
        self._items[item.id] = item

    def list_by_purchase(self, purchase_id: int) -> list[object]:
        return [i for i in self._items.values() if i.purchase_id == purchase_id]


def test_register_purchase_requires_permission() -> None:
    repo = FakePurchaseRepository()
    item_repo = FakePurchaseItemRepository()

    with pytest.raises(PermissionDenied, match=re.escape("catalog.cost.update")):
        RegisterPurchase(repo, item_repo, set()).execute(
            RegisterPurchaseInput(
                supplier_id=None,
                items=[
                    PurchaseItemInput(
                        product_id=1,
                        quantity_thousandths=1000,
                        unit_cost_cents=1000,
                    ),
                ],
                user_id=1,
                username="caixa",
                company_id=1,
            )
        )


def test_register_purchase_success() -> None:
    repo = FakePurchaseRepository()
    item_repo = FakePurchaseItemRepository()

    output = RegisterPurchase(repo, item_repo, {"catalog.cost.update"}).execute(
        RegisterPurchaseInput(
            supplier_id=1,
            items=[
                PurchaseItemInput(product_id=1, quantity_thousandths=1000, unit_cost_cents=1000),
                PurchaseItemInput(product_id=2, quantity_thousandths=2000, unit_cost_cents=500),
            ],
            user_id=1,
            username="gerente",
            company_id=1,
        )
    )
    assert output.purchase_id == 1
    assert output.total_cents == 2000  # 1000*1000/1000 + 2000*500/1000 = 1000 + 1000


def test_register_purchase_empty_items() -> None:
    repo = FakePurchaseRepository()
    item_repo = FakePurchaseItemRepository()

    with pytest.raises(ValidationError, match="pelo menos um item"):
        RegisterPurchase(repo, item_repo, {"catalog.cost.update"}).execute(
            RegisterPurchaseInput(
                supplier_id=None,
                items=[],
                user_id=1,
                username="gerente",
                company_id=1,
            )
        )


def test_count_inventory_requires_permission() -> None:
    with pytest.raises(PermissionDenied, match=re.escape("catalog.cost.update")):
        CountInventory(set()).execute(
            InventoryCountInput(
                product_id=1,
                counted_quantity_thousandths=5000,
                reason="contagem física",
                user_id=1,
                username="caixa",
                company_id=1,
            )
        )


def test_count_inventory_success() -> None:
    output = CountInventory({"catalog.cost.update"}).execute(
        InventoryCountInput(
            product_id=1,
            counted_quantity_thousandths=5000,
            reason="contagem física mensal",
            user_id=1,
            username="gerente",
            company_id=1,
        )
    )
    assert output.product_id == 1
    assert output.counted_quantity_thousandths == 5000
    assert output.difference_thousandths == 5000
    assert output.reason == "contagem física mensal"


def test_count_inventory_requires_reason() -> None:
    with pytest.raises(ValidationError, match="obrigatório"):
        CountInventory({"catalog.cost.update"}).execute(
            InventoryCountInput(
                product_id=1,
                counted_quantity_thousandths=5000,
                reason="",
                user_id=1,
                username="gerente",
                company_id=1,
            )
        )
