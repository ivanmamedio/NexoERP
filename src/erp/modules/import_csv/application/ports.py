"""Application ports for import CSV module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.import_csv.domain.import_result import (
    ImportResult,
)


@runtime_checkable
class ProductSnapshot(Protocol):
    """Snapshot de produto para importação via port do catálogo."""

    sku: str
    name: str
    description: str
    unit: str
    cost_cents: int
    margin_pct: int
    price_cents: int
    stock_qty: int
    min_stock_qty: int
    sold_by_weight: bool
    active: bool
    company_id: int


@runtime_checkable
class ProductCatalogPort(Protocol):
    """Port para acesso ao catálogo de produtos durante importação."""

    def get_by_sku(self, sku: str, company_id: int | None = None) -> object | None: ...
    def list_all_skus(self, company_id: int | None = None) -> list[str]: ...
    def add(self, product: ProductSnapshot) -> None: ...
    def add_snapshot(self, product: ProductSnapshot) -> None: ...
    def commit(self) -> None: ...


@runtime_checkable
class ImportResultRepositoryPort(Protocol):
    """Port para persistência de resultados de importação."""

    def save_result(self, result: ImportResult) -> None: ...
    def get_result(self, import_id: int) -> ImportResult | None: ...
