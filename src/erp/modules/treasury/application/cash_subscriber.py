"""Subscriber da tesouraria que reage a eventos de caixa.

Cria lançamentos financeiros para sangrias e suprimentos.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sqlalchemy.engine import Engine

from erp.modules.treasury.application.ports import FinancialEntryRepository
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.infrastructure.unit_of_work import (
    SqlAlchemyTreasuryUnitOfWork,
)
from erp.shared.application.events import EventBus


@runtime_checkable
class CashSessionData(Protocol):
    """Dados mínimos de sessão de caixa consumidos pela tesouraria."""

    company_id: int
    id: int
    register_id: str | None
    opening_amount_cents: int
    closing_amount_cents: int | None
    difference_cents: int | None


class TreasuryCashSubscriber:
    """Reage a eventos de caixa (abertura, sangria, suprimento, fechamento)."""

    def __init__(self, event_bus: EventBus, engine: Engine) -> None:
        self._event_bus = event_bus
        self._engine = engine
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe("cash_session_opened", self._on_cash_session_opened)
        self._event_bus.subscribe("cash_sangria", self._on_cash_sangria)
        self._event_bus.subscribe("cash_suprimento", self._on_cash_suprimento)
        self._event_bus.subscribe("cash_session_closed", self._on_cash_session_closed)

    def _on_cash_session_opened(self, session: CashSessionData) -> None:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=session.company_id,
                type="cash_opening",
                amount_cents=session.opening_amount_cents,
                source_type="cash_session",
                source_id=session.id,
                description=f"Abertura de caixa (terminal {session.register_id})",
            )
            repo.add(entry)
            uow.commit()

    def _on_cash_sangria(self, event: Any) -> None:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=event.company_id,
                type="cash_sangria",
                amount_cents=event.amount_cents,
                source_type="cash_sangria",
                source_id=event.session_id,
                description=event.description or "Sangria de caixa",
            )
            repo.add(entry)
            uow.commit()

    def _on_cash_suprimento(self, event: Any) -> None:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=event.company_id,
                type="cash_suprimento",
                amount_cents=event.amount_cents,
                source_type="cash_suprimento",
                source_id=event.session_id,
                description=event.description or "Suprimento de caixa",
            )
            repo.add(entry)
            uow.commit()

    def _on_cash_session_closed(self, session: CashSessionData) -> None:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            repo: FinancialEntryRepository = uow.financial_entries
            entry = FinancialEntry(
                company_id=session.company_id,
                type="cash_closing",
                amount_cents=session.closing_amount_cents or 0,
                source_type="cash_session",
                source_id=session.id,
                description=f"Fechamento de caixa (diferença: {session.difference_cents or 0})",
            )
            repo.add(entry)
            uow.commit()