"""Application ports for the sales module."""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.modules.sales.domain.sale_payment import SalePayment


@runtime_checkable
class ProductSnapshot(Protocol):
    """Leitura mínima de produto do catálogo consumida pelo módulo de vendas."""

    id: int
    sku: str
    name: str
    active: bool
    price_cents: int
    stock_qty: int
    unit: str


@runtime_checkable
class ProductCatalogPort(Protocol):
    """Port de leitura/gravação de produto do catálogo (sem expor domain do catalog)."""

    def get_by_sku(self, sku: str, company_id: int | None = None) -> ProductSnapshot | None: ...
    def search(
        self, query: str, company_id: int | None = None, limit: int = 20
    ) -> list[ProductSnapshot]: ...
    def get_by_id(self, product_id: int) -> ProductSnapshot | None: ...
    def save(self, product: ProductSnapshot) -> None: ...


@runtime_checkable
class SaleRepository(Protocol):
    def add(self, sale: Sale) -> None: ...
    def save(self, sale: Sale) -> None: ...
    def get_by_id(self, sale_id: int, company_id: int | None = None) -> Sale | None: ...
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
class SupervisorAuthInfo(Protocol):
    """Resultado mínimo de autenticação de supervisor."""

    user_id: int
    username: str


@runtime_checkable
class SupervisorAuthPort(Protocol):
    """Port para autenticar supervisor e verificar permissão de desconto."""

    def authenticate(self, username: str, password: str) -> SupervisorAuthInfo | None: ...
    def check_permission(self, *, user_id: int, permission_code: str) -> bool: ...


@runtime_checkable
class CatalogUnitOfWork(Protocol):
    """Unit of Work port for catalog module (used by sales for stock updates)."""

    products: ProductCatalogPort | None

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
