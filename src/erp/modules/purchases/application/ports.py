"""Application ports for the purchases module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.purchases.domain.purchase import Purchase, PurchaseItem


@runtime_checkable
class PurchaseRepository(Protocol):
    """Repository port for Purchase aggregates."""

    def add(self, purchase: Purchase) -> None: ...
    def save(self, purchase: Purchase) -> None: ...
    def get_by_id(self, purchase_id: int) -> Purchase | None: ...
    def list_by_company(self, company_id: int) -> list[Purchase]: ...


@runtime_checkable
class PurchaseItemRepository(Protocol):
    """Repository port for PurchaseItem aggregates."""

    def add(self, item: PurchaseItem) -> None: ...
    def save(self, item: PurchaseItem) -> None: ...
    def list_by_purchase(self, purchase_id: int) -> list[PurchaseItem]: ...
