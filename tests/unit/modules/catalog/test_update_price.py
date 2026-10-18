"""Unit tests for UpdatePrice use case (permission + audit event)."""

from __future__ import annotations

import pytest

from erp.modules.catalog.application.update_price import (
    UpdatePrice,
    UpdatePriceInput,
)
from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.application.events import EventBus
from erp.shared.domain.errors import PermissionDenied


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


class FakeEventBus(EventBus):
    def __init__(self) -> None:
        super().__init__()
        self.published: list = []

    def publish(self, event) -> None:  # type: ignore[override]
        self.published.append(event)


def test_update_price_requires_permission() -> None:
    repo = FakeProductRepository()
    product = Product(
        id=1, sku="P001", name="Produto", unit="un", price_cents=1000, company_id=1
    )
    repo.add(product)

    bus = FakeEventBus()
    # Caixa não tem product.price.update
    uc = UpdatePrice(repo, bus, user_permissions={"sale.cancel"})

    with pytest.raises(PermissionDenied, match="product.price.update"):
        uc.execute(
            UpdatePriceInput(
                product_id=1,
                new_price_cents=1500,
                user_id=1,
                username="caixa",
                company_id=1,
            )
        )


def test_update_price_success_emits_event() -> None:
    repo = FakeProductRepository()
    product = Product(
        id=1, sku="P001", name="Produto", unit="un", price_cents=1000, company_id=1
    )
    repo.add(product)

    bus = FakeEventBus()
    uc = UpdatePrice(repo, bus, user_permissions={"product.price.update"})

    output = uc.execute(
        UpdatePriceInput(
            product_id=1,
            new_price_cents=1500,
            user_id=1,
            username="admin",
            reason="reajuste",
            company_id=1,
        )
    )

    assert output.old_price_cents == 1000
    assert output.product.price_cents == 1500
    assert len(bus.published) == 1
    event = bus.published[0]
    assert event.entity_type == "Product"
    assert event.entity_id == 1
    assert event.after == {"price_cents": 1500}
    assert event.before == {"price_cents": 1000}
