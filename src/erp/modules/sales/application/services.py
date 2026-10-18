"""Application services facade for Sales."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.catalog.infrastructure.unit_of_work import (
    SqlAlchemyCatalogUnitOfWork,
)
from erp.modules.sales.application.add_item import AddItem, AddItemInput, AddItemOutput
from erp.modules.sales.application.apply_discount import (
    ApplyDiscount,
    ApplyDiscountInput,
    ApplyDiscountOutput,
)
from erp.modules.sales.application.cancel_sale import (
    CancelItem,
    CancelItemInput,
    CancelSale,
    CancelSaleInput,
)
from erp.modules.sales.application.finalize_sale import (
    FinalizeSale,
    FinalizeSaleInput,
    FinalizeSaleOutput,
)
from erp.modules.sales.application.start_sale import (
    StartSale,
    StartSaleInput,
    StartSaleOutput,
)
from erp.modules.sales.infrastructure.unit_of_work import SqlAlchemySalesUnitOfWork
from erp.shared.application.events import EventBus


class SalesServices:
    """Facade de casos de uso de vendas. Venda + estoque é atômico (mesma UoW)."""

    def __init__(
        self,
        engine: Engine,
        catalog_engine: Engine | None,
        event_bus: EventBus,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._engine = engine
        self._catalog_engine = catalog_engine if catalog_engine is not None else engine
        self._event_bus = event_bus
        self._user_permissions = user_permissions or set()

    def start_sale(self, input: StartSaleInput) -> StartSaleOutput:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow:
            assert uow.sales is not None
            result = StartSale(uow.sales).execute(input)
            uow.commit()
            return result

    def add_item(self, input: AddItemInput) -> AddItemOutput:
        # Nota: duas UoWs no mesmo engine; ambas fazem commit em sequência.
        # Falha durante execute() desfaz tudo (nenhum commit ocorre).
        with SqlAlchemySalesUnitOfWork(self._engine) as uow, SqlAlchemyCatalogUnitOfWork(
            self._catalog_engine
        ) as catalog_uow:
            assert uow.sales is not None and uow.items is not None
            assert catalog_uow.products is not None
            result = AddItem(uow.sales, uow.items, catalog_uow.products).execute(input)
            catalog_uow.commit()
            uow.commit()
            return result

    def apply_discount(self, input: ApplyDiscountInput) -> ApplyDiscountOutput:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow:
            assert uow.sales is not None
            result = ApplyDiscount(uow.sales, self._user_permissions).execute(input)
            uow.commit()
            return result

    def finalize_sale(self, input: FinalizeSaleInput) -> FinalizeSaleOutput:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow, SqlAlchemyCatalogUnitOfWork(
            self._catalog_engine
        ) as catalog_uow:
            assert uow.sales is not None and uow.items is not None
            assert uow.payments is not None
            assert catalog_uow.products is not None
            result = FinalizeSale(
                uow.sales, uow.items, uow.payments, catalog_uow.products, self._event_bus
            ).execute(input)
            catalog_uow.commit()
            uow.commit()
            return result

    def cancel_sale(self, input: CancelSaleInput) -> None:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow, SqlAlchemyCatalogUnitOfWork(
            self._catalog_engine
        ) as catalog_uow:
            assert uow.sales is not None and uow.items is not None
            assert catalog_uow.products is not None
            CancelSale(uow.sales, uow.items, catalog_uow.products, self._user_permissions).execute(
                input
            )
            catalog_uow.commit()
            uow.commit()

    def cancel_item(self, input: CancelItemInput) -> None:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow:
            assert uow.sales is not None and uow.items is not None
            CancelItem(uow.sales, uow.items, self._user_permissions).execute(input)
            uow.commit()
