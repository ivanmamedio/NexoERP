"""Subscriber do caixa que reage a SaleCompleted.

Registra um movimento de venda_dinheiro e atualiza os totais da sessão
de caixa aberta para o terminal da venda.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.cash.application.ports import (
    CashMovementRepository,
    CashSessionRepository,
)
from erp.modules.cash.domain.cash_movement import CashMovement, MovementType
from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


class CashSaleSubscriber:
    """Reage a SaleCompleted registrando movimento de caixa e atualizando a sessão."""

    def __init__(self, event_bus: EventBus, engine: Engine) -> None:
        self._event_bus = event_bus
        self._engine = engine
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(SaleCompleted, self._on_sale_completed)

    def _on_sale_completed(self, event: SaleCompleted) -> None:
        if event.session_id is None:
            return

        with SqlAlchemyCashUnitOfWork(self._engine) as uow:
            assert uow.movements is not None
            assert uow.sessions is not None

            movements: CashMovementRepository = uow.movements
            sessions: CashSessionRepository = uow.sessions

            # Registra movimento de venda em dinheiro (se houver)
            if event.cash_cents > 0:
                movement = CashMovement(
                    session_id=event.session_id,
                    company_id=event.company_id,
                    movement_type=MovementType.VENDA_DINHEIRO,
                    amount_cents=event.cash_cents,
                    description=f"Venda {event.sale_id}",
                    user_id=event.user_id,
                    username=event.username,
                )
                movements.add(movement)

            # Atualiza totais da sessão de caixa aberta
            session = sessions.get_by_id(event.session_id)
            if session is not None and session.is_open():
                session.total_sales_cents += event.cash_cents
                session.total_pix_cents += event.pix_cents
                session.total_card_cents += event.card_cents
                sessions.save(session)

            uow.commit()
