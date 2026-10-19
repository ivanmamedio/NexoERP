"""Subscriber do catálogo que reage a SaleCompleted.

Cria movimentos de estoque (tipo 'sale') para cada item da venda finalizada,
usando os dados do próprio evento (sem consultar infra de sales).
"""

from __future__ import annotations

from typing import cast

from sqlalchemy.engine import Engine

from erp.modules.catalog.application.ports import StockMovementRepository
from erp.modules.catalog.domain.stock_movement import StockMovement
from erp.modules.catalog.infrastructure.unit_of_work import (
    SqlAlchemyCatalogUnitOfWork,
)
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


class CatalogSaleSubscriber:
    """Reage a SaleCompleted registrando movimentos de estoque de saída."""

    def __init__(self, event_bus: EventBus, engine: Engine) -> None:
        self._event_bus = event_bus
        self._engine = engine
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(SaleCompleted, self._on_sale_completed)

    def _on_sale_completed(self, event: SaleCompleted) -> None:
        with SqlAlchemyCatalogUnitOfWork(self._engine) as cat_uow:
            assert cat_uow.stock_movements is not None
            repo: StockMovementRepository = cat_uow.stock_movements
            for item in event.items:
                product_id = cast(int | None, item.get("product_id"))
                qty = cast(int, item.get("quantity_thousandths", 0))
                if product_id is None:
                    continue
                movement = StockMovement(
                    product_id=product_id,
                    company_id=event.company_id,
                    quantity_thousandths=-abs(qty),
                    movement_type="sale",
                    reference_id=event.sale_id,
                    notes=f"Venda {event.sale_id}",
                    user_id=event.user_id,
                    username=event.username,
                )
                repo.add(movement)
            cat_uow.commit()
