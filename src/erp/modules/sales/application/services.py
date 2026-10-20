"""Application services facade for Sales."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.engine import Engine

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
from erp.modules.sales.application.get_sale_state import (
    GetSaleState,
    SaleStateOutput,
)
from erp.modules.sales.application.ports import CatalogUnitOfWork
from erp.modules.sales.application.search_products import (
    ProductSearchItem,
    SearchProducts,
)
from erp.modules.sales.application.start_sale import (
    StartSale,
    StartSaleInput,
    StartSaleOutput,
)
from erp.modules.sales.infrastructure.unit_of_work import SqlAlchemySalesUnitOfWork
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


class SalesServices:
    """Facade de casos de uso de vendas. Venda + estoque é atômico (mesma UoW)."""

    def __init__(
        self,
        engine: Engine,
        catalog_uow_factory: Callable[[], CatalogUnitOfWork],
        event_bus: EventBus,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._engine = engine
        self._catalog_uow_factory = catalog_uow_factory
        self._event_bus = event_bus
        self._user_permissions = user_permissions or set()

    def set_user_permissions(self, permissions: set[str]) -> None:
        """Atualiza as permissões do operador logado (chamado após o login)."""
        self._user_permissions = permissions

    def start_sale(self, input: StartSaleInput) -> StartSaleOutput:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow:
            assert uow.sales is not None
            result = StartSale(uow.sales).execute(input)
            uow.commit()
            return result

    def add_item(self, input: AddItemInput) -> AddItemOutput:
        with (
            SqlAlchemySalesUnitOfWork(self._engine) as uow,
            self._catalog_uow_factory() as catalog_uow,
        ):
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
        sale_items_data: list[dict[str, object]] = []
        with (
            SqlAlchemySalesUnitOfWork(self._engine) as uow,
            self._catalog_uow_factory() as catalog_uow,
        ):
            assert uow.sales is not None and uow.items is not None
            assert uow.payments is not None
            assert catalog_uow.products is not None
            result = FinalizeSale(uow.sales, uow.items, uow.payments, catalog_uow.products).execute(
                input
            )
            items = uow.items.list_by_sale(result.sale.id or 0)
            sale_items_data = [
                {
                    "product_id": i.product_id,
                    "quantity_thousandths": i.quantity_thousandths,
                }
                for i in items
                if not i.cancelled and i.product_id is not None
            ]
            catalog_uow.commit()
            uow.commit()

        sale = result.sale
        cash_paid = sum(p.amount_cents for p in input.payments if p.method == "cash")
        pix_cents = sum(p.amount_cents for p in input.payments if p.method == "pix")
        card_cents = sum(p.amount_cents for p in input.payments if p.method == "card")
        self._event_bus.publish(
            SaleCompleted(
                sale_id=sale.id or 0,
                company_id=sale.company_id,
                session_id=sale.session_id,
                user_id=input.user_id,
                username=input.username,
                total_cents=sale.total_cents,
                cash_cents=cash_paid,
                pix_cents=pix_cents,
                card_cents=card_cents,
                items=sale_items_data,
            )
        )
        return result

    def cancel_sale(self, input: CancelSaleInput) -> None:
        with (
            SqlAlchemySalesUnitOfWork(self._engine) as uow,
            self._catalog_uow_factory() as catalog_uow,
        ):
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

    def get_sale_state(self, *, sale_id: int) -> SaleStateOutput:
        with SqlAlchemySalesUnitOfWork(self._engine) as uow:
            assert uow.sales is not None and uow.items is not None
            return GetSaleState(uow.sales, uow.items).execute(sale_id)

    def search_products(
        self, *, query: str, company_id: int | None = None, limit: int = 10
    ) -> list[ProductSearchItem]:
        with self._catalog_uow_factory() as catalog_uow:
            assert catalog_uow.products is not None
            return SearchProducts(catalog_uow.products).execute(
                query=query, company_id=company_id, limit=limit
            )
