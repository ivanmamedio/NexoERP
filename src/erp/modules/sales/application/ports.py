"""Application ports for the sales module."""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.modules.sales.domain.sale_payment import SalePayment


@runtime_checkable
class SaleRepository(Protocol):
    def add(self, sale: Sale) -> None: ...
    def save(self, sale: Sale) -> None: ...
    def get_by_id(self, sale_id: int) -> Sale | None: ...
    def list_open(self, company_id: int | None = None) -> list[Sale]: ...


@runtime_checkable
class SaleItemRepository(Protocol):
    def add(self, item: SaleItem) -> None: ...
    def save(self, item: SaleItem) -> None: ...
    def get_by_id(self, item_id: int) -> SaleItem | None: ...
    def list_by_sale(self, sale_id: int) -> list[SaleItem]: ...


@runtime_checkable
class SalePaymentRepository(Protocol):
    def add(self, payment: SalePayment) -> None: ...
    def list_by_sale(self, sale_id: int) -> list[SalePayment]: ...


@runtime_checkable
class CatalogUnitOfWork(Protocol):
    """Unit of Work port for catalog module (used by sales for stock updates)."""

    products: ProductRepository | None

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
