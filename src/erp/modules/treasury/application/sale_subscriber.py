"""Subscriber da tesouraria que reage a SaleCompleted.

Cria um lançamento financeiro (receivable) para cada venda finalizada.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.treasury.application.ports import FinancialEntryRepository
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.infrastructure.unit_of_work import (
    SqlAlchemyTreasuryUnitOfWork,
)
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


class TreasurySaleSubscriber:
    """Reage a SaleCompleted criando lançamento financeiro de recebimento."""

    def __init__(self, event_bus: EventBus, engine: Engine) -> None:
        self._event_bus = event_bus
        self._engine = engine
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(SaleCompleted, self._on_sale_completed)

    def _on_sale_completed(self, event: SaleCompleted) -> None:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=event.company_id,
                type="receivable",
                amount_cents=event.total_cents,
                source_type="sale",
                source_id=event.sale_id,
                description=f"Venda {event.sale_id}",
            )
            repo.add(entry)
            uow.commit()
