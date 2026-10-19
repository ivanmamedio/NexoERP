"""Unit tests for TreasurySaleSubscriber."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.treasury.application.sale_subscriber import TreasurySaleSubscriber
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.infrastructure.models import (
    Base,
    FinancialEntryModel,
)
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_treasury_sale_subscriber_creates_receivable(engine) -> None:
    event_bus = EventBus()
    TreasurySaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=1,
        company_id=1,
        session_id=1,
        user_id=1,
        username="caixa",
        total_cents=5000,
        cash_cents=3000,
        pix_cents=1000,
        card_cents=1000,
    )
    event_bus.publish(event)

    with Session(engine) as session:
        entries = session.query(FinancialEntryModel).all()
        assert len(entries) == 1
        assert entries[0].type == "receivable"
        assert entries[0].amount_cents == 5000
        assert entries[0].company_id == 1
        assert entries[0].source_type == "sale"
        assert entries[0].source_id == 1
        assert entries[0].description == "Venda 1"

    # Domain-level check via repository
    from erp.modules.treasury.infrastructure.repository import (
        SqlAlchemyFinancialEntryRepository,
    )
    from erp.shared.infrastructure.database import get_session_factory

    factory = get_session_factory(engine)
    with factory() as session:
        repo = SqlAlchemyFinancialEntryRepository(session)
        entries = repo.list_by_company(1)
        assert len(entries) == 1
        assert isinstance(entries[0], FinancialEntry)
        assert entries[0].amount_cents == 5000


def test_treasury_sale_subscriber_zero_total(engine) -> None:
    event_bus = EventBus()
    TreasurySaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=2,
        company_id=1,
        session_id=None,
        user_id=1,
        username="caixa",
        total_cents=0,
        cash_cents=0,
        pix_cents=0,
        card_cents=0,
    )
    event_bus.publish(event)

    with Session(engine) as session:
        entries = session.query(FinancialEntryModel).all()
        assert len(entries) == 1
        assert entries[0].amount_cents == 0
