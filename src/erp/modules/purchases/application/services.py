"""Application services facade for Purchases."""

from __future__ import annotations

from typing import cast

from sqlalchemy.engine import Engine

from erp.modules.purchases.application.count_inventory import (
    CountInventory,
    InventoryCountInput,
    InventoryCountOutput,
)
from erp.modules.purchases.application.register_purchase import (
    PurchaseItemInput,
    RegisterPurchase,
    RegisterPurchaseInput,
    RegisterPurchaseOutput,
)
from erp.modules.purchases.infrastructure.unit_of_work import (
    SqlAlchemyPurchasesUnitOfWork,
)


class PurchasesServices:
    """Facade de casos de uso de compras sobre SQLAlchemy."""

    def __init__(
        self,
        engine: Engine,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._engine = engine
        self._user_permissions = user_permissions or set()

    def register_purchase(
        self,
        *,
        supplier_id: int | None,
        items: list[dict[str, object]],
        user_id: int | None,
        username: str,
        company_id: int | None = None,
    ) -> RegisterPurchaseOutput:
        with SqlAlchemyPurchasesUnitOfWork(self._engine) as uow:
            assert uow.purchases is not None and uow.purchase_items is not None
            item_inputs = [
                PurchaseItemInput(
                    product_id=cast(int, it["product_id"]),
                    quantity_thousandths=cast(int, it["quantity_thousandths"]),
                    unit_cost_cents=cast(int, it["unit_cost_cents"]),
                )
                for it in items
            ]
            result = RegisterPurchase(
                uow.purchases, uow.purchase_items, self._user_permissions
            ).execute(
                RegisterPurchaseInput(
                    supplier_id=supplier_id,
                    items=item_inputs,
                    user_id=user_id,
                    username=username,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def count_inventory(
        self,
        *,
        product_id: int,
        counted_quantity_thousandths: int,
        reason: str,
        user_id: int | None = None,
        username: str = "",
        company_id: int | None = None,
    ) -> InventoryCountOutput:
        with SqlAlchemyPurchasesUnitOfWork(self._engine) as uow:
            assert uow.purchases is not None
            result = CountInventory(self._user_permissions).execute(
                InventoryCountInput(
                    product_id=product_id,
                    counted_quantity_thousandths=counted_quantity_thousandths,
                    reason=reason,
                    user_id=user_id,
                    username=username,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def set_user_permissions(self, permissions: set[str]) -> None:
        """Atualiza as permissões do operador logado."""
        self._user_permissions = permissions
