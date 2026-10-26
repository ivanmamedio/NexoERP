"""Subscriber da tesouraria que reage a eventos de caixa.

Cria lançamentos financeiros para fechamento de caixa.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.treasury.application.ports import FinancialEntryRepository
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.infrastructure.unit_of_work import (
    SqlAlchemyTreasuryUnitOfWork,
)
from erp.shared.application.events import EventBus
from erp.shared.domain.events import CashSessionClosed


class TreasuryCashSubscriber:
    """Reage a evento de fechamento de caixa."""

    def __init__(self, event_bus: EventBus, engine: Engine) -> None:
        self._event_bus = event_bus
        self._engine = engine
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(CashSessionClosed, self._on_cash_session_closed)

    def _on_cash_session_closed(self, session: CashSessionClosed) -> None:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=session.company_id,
                type="cash_closing",
                amount_cents=session.closing_amount_cents or 0,
                source_type="cash_session",
                source_id=session.session_id,
                description=f"Fechamento de caixa (diferença: {session.difference_cents or 0})",
            )
            repo.add(entry)
            uow.commit()