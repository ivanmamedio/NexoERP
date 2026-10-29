"""Subscriber da tesouraria que reage a vendas fiadas (crédito).

Gera uma receivable no treasury quando uma venda tem pagamento a crédito.
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


class TreasuryCreditSubscriber:
    """Reage a vendas fiadas criando lançamentos a receber."""

    def __init__(self, event_bus: EventBus, engine: Engine) -> None:
        self._event_bus = event_bus
        self._engine = engine
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(SaleCompleted, self._on_sale_completed)

    def _on_sale_completed(self, event: SaleCompleted) -> None:
        if event.credit_cents <= 0:
            return

        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=event.company_id,
                type="receivable",
                amount_cents=event.credit_cents,
                source_type="sale_credit",
                source_id=event.sale_id,
                description=f"Venda a crédito {event.sale_id}",
            )
            repo.add(entry)
            uow.commit()
