"""Application services facade for Catalog."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.engine import Engine

from erp.modules.catalog.application.adjust_stock import (
    AdjustStock,
    AdjustStockInput,
    AdjustStockOutput,
)
from erp.modules.catalog.application.create_product import (
    CreateProduct,
    CreateProductInput,
    CreateProductOutput,
)
from erp.modules.catalog.application.list_low_stock import (
    ListLowStock,
    ListLowStockOutput,
)
from erp.modules.catalog.application.update_price import (
    UpdatePrice,
    UpdatePriceInput,
    UpdatePriceOutput,
)
from erp.modules.catalog.application.update_product import (
    UpdateProduct,
    UpdateProductInput,
    UpdateProductOutput,
)
from erp.modules.catalog.infrastructure.unit_of_work import (
    SqlAlchemyCatalogUnitOfWork,
)
from erp.shared.application.events import EventBus


@runtime_checkable
class CatalogServices(Protocol):
    """Facade de casos de uso de catálogo sobre SQLAlchemy (1 transação por operação)."""

    def create_product(self, input: CreateProductInput) -> CreateProductOutput: ...
    def update_product(self, input: UpdateProductInput) -> UpdateProductOutput: ...
    def update_price(self, input: UpdatePriceInput) -> UpdatePriceOutput: ...
    def adjust_stock(self, input: AdjustStockInput) -> AdjustStockOutput: ...
    def list_low_stock(self, *, company_id: int | None = None) -> ListLowStockOutput: ...


class SqlAlchemyCatalogServices:
    """Implementação concreta do facade CatalogServices."""

    def __init__(
        self,
        engine: Engine,
        event_bus: EventBus,
        user_permissions: set[str],
    ) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._user_permissions = user_permissions

    def create_product(self, input: CreateProductInput) -> CreateProductOutput:
        with SqlAlchemyCatalogUnitOfWork(self._engine) as uow:
            assert uow.products is not None
            result = CreateProduct(uow.products).execute(input)
            uow.commit()
            return result

    def update_product(self, input: UpdateProductInput) -> UpdateProductOutput:
        with SqlAlchemyCatalogUnitOfWork(self._engine) as uow:
            assert uow.products is not None
            result = UpdateProduct(uow.products).execute(input)
            uow.commit()
            return result

    def update_price(self, input: UpdatePriceInput) -> UpdatePriceOutput:
        with SqlAlchemyCatalogUnitOfWork(self._engine) as uow:
            assert uow.products is not None
            result = UpdatePrice(
                uow.products, self._event_bus, self._user_permissions
            ).execute(input)
            uow.commit()
            return result

    def adjust_stock(self, input: AdjustStockInput) -> AdjustStockOutput:
        with SqlAlchemyCatalogUnitOfWork(self._engine) as uow:
            assert uow.products is not None
            result = AdjustStock(uow.products).execute(input)
            uow.commit()
            return result

    def list_low_stock(self, *, company_id: int | None = None) -> ListLowStockOutput:
        with SqlAlchemyCatalogUnitOfWork(self._engine) as uow:
            assert uow.products is not None
            return ListLowStock(uow.products).execute(company_id=company_id)
