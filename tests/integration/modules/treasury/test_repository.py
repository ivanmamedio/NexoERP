"""Integration tests for treasury repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.domain.payable import Payable
from erp.modules.treasury.domain.receivable import Receivable
from erp.modules.treasury.infrastructure.models import Base
from erp.modules.treasury.infrastructure.repository import (
    SqlAlchemyFinancialEntryRepository,
    SqlAlchemyPayableRepository,
    SqlAlchemyReceivableRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


def _make_entry(
    type_: str,
    amount_cents: int,
    company_id: int = 1,
    days_ago: int = 0,
) -> FinancialEntry:
    return FinancialEntry(
        company_id=company_id,
        type=type_,
        amount_cents=amount_cents,
        source_type="sale",
        source_id=1,
        description="teste",
        date=datetime.now(UTC) - timedelta(days=days_ago),
    )


def test_financial_entry_crud(session: Session) -> None:
    """CRUD completo de lançamentos financeiros."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    entry = _make_entry("sale", 10000, company_id=1)
    repo.add(entry)
    session.commit()

    assert entry.id is not None
    assert entry.id > 0

    # Recuperar
    entries = repo.list_by_company(1)
    assert len(entries) == 1
    assert entries[0].type == "sale"
    assert entries[0].amount_cents == 10000
    assert entries[0].company_id == 1


def test_financial_entry_list_by_period(session: Session) -> None:
    """Filtro por período funciona corretamente."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    now = datetime.now(UTC)
    repo.add(_make_entry("sale", 10000, company_id=1, days_ago=0))
    repo.add(_make_entry("sale", 20000, company_id=1, days_ago=5))
    repo.add(_make_entry("sale", 30000, company_id=1, days_ago=10))
    session.commit()

    # Últimos 3 dias
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    entries = repo.list_by_period(start_date=start, end_date=end, company_id=1)
    assert len(entries) == 1
    assert entries[0].amount_cents == 10000


def test_isolation_between_companies(session: Session) -> None:
    """Lançamentos da empresa A não aparecem para a empresa B."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    repo.add(_make_entry("sale", 10000, company_id=1))
    repo.add(_make_entry("sale", 20000, company_id=2))
    session.commit()

    entries_1 = repo.list_by_company(1)
    entries_2 = repo.list_by_company(2)

    assert len(entries_1) == 1
    assert entries_1[0].amount_cents == 10000
    assert len(entries_2) == 1
    assert entries_2[0].amount_cents == 20000


def test_payable_crud(session: Session) -> None:
    """CRUD de contas a pagar com parcelas."""
    repo = SqlAlchemyPayableRepository(session)

    payable = Payable(
        company_id=1,
        supplier_id=10,
        description="Compra de mercadoria",
        total_amount_cents=30000,
        source_type="purchase",
        source_id=1,
    )
    payable.add_installment(1, datetime.now(UTC) + timedelta(days=30), 15000)
    payable.add_installment(2, datetime.now(UTC) + timedelta(days=60), 15000)

    repo.add(payable)
    session.commit()

    assert payable.id is not None

    saved = repo.get_by_id(payable.id)
    assert saved is not None
    assert saved.total_amount_cents == 30000
    assert len(saved.installments) == 2


def test_receivable_crud(session: Session) -> None:
    """CRUD de contas a receber."""
    repo = SqlAlchemyReceivableRepository(session)

    receivable = Receivable(
        company_id=1,
        customer_id=20,
        description="Venda a prazo",
        total_amount_cents=25000,
        due_date=datetime.now(UTC) + timedelta(days=15),
        source_type="sale",
        source_id=5,
    )
    repo.add(receivable)
    session.commit()

    assert receivable.id is not None

    saved = repo.get_by_id(receivable.id)
    assert saved is not None
    assert saved.total_amount_cents == 25000
    assert saved.pending_amount_cents == 25000

    # Receber pagamento parcial
    saved.receive(10000, datetime.now(UTC))
    repo.save(saved)
    session.commit()

    reloaded = repo.get_by_id(receivable.id)
    assert reloaded is not None
    assert reloaded.received_amount_cents == 10000
    assert reloaded.pending_amount_cents == 15000
    assert reloaded.status == "partial"
