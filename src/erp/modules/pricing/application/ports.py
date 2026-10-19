"""Application ports for the pricing module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.catalog.domain.product import Product


@runtime_checkable
class ProductRepository(Protocol):
    """Port for reading product data (used by pricing calculator)."""

    def get_by_id(self, product_id: int) -> Product | None: ...
    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None: ...
    def list_all(self, company_id: int | None = None) -> list[Product]: ...


@runtime_checkable
class ProductPriceUpdaterPort(Protocol):
    """Port for updating product prices (implemented by catalog module)."""

    def update_price(
        self,
        *,
        product_id: int,
        new_price_cents: int,
        user_id: int | None,
        username: str,
        reason: str = "",
        company_id: int | None = None,
    ) -> None: ...