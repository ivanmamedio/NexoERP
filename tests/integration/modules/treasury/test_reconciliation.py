"""Integration tests for cash flow reconciliation using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.treasury.application.get_cash_flow import (
    CashFlowInput,
    GetCashFlow,
)
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.infrastructure.models import Base
from erp.modules.treasury.infrastructure.repository import (
    SqlAlchemyFinancialEntryRepository,
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


def test_cash_flow_reconciliation_includes_sangria(session: Session) -> None:
    """Reconciliação: fluxo = vendas + recebíveis - pagáveis - sangrias + suprimentos no período."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    now = datetime.now(UTC)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Vendas: +100,00
    repo.add(_make_entry("sale", 10000, company_id=1))
    # Recebíveis: +50,00
    repo.add(_make_entry("receivable", 5000, company_id=1))
    # Pagáveis: -30,00
    repo.add(_make_entry("payable", 3000, company_id=1))
    # Sangria: -20,00 (dinheiro saindo do caixa - valor negativo)
    repo.add(_make_entry("cash_sangria", -2000, company_id=1))
    # Suprimento: +10,00 (dinheiro entrando no caixa)
    repo.add(_make_entry("cash_suprimento", 1000, company_id=1))
    session.commit()

    output = GetCashFlow(repo).execute(CashFlowInput(start_date=start, end_date=end, company_id=1))

    assert output.total_sales_cents == 10000
    assert output.total_receivables_cents == 5000
    assert output.total_payables_cents == 3000
    assert output.total_cash_movements_cents == -1000  # -2000 (sangria) + 1000 (suprimento)

    # net_flow = 10000 + 5000 - 3000 + (-1000) = 11000
    assert output.net_flow_cents == 11000


def test_cash_flow_reconciliation_without_cash_movements(session: Session) -> None:
    """Quando não há movimentos de caixa, net = vendas + recebíveis - pagáveis."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    now = datetime.now(UTC)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    repo.add(_make_entry("sale", 10000, company_id=1))
    repo.add(_make_entry("receivable", 5000, company_id=1))
    repo.add(_make_entry("payable", 3000, company_id=1))
    session.commit()

    output = GetCashFlow(repo).execute(CashFlowInput(start_date=start, end_date=end, company_id=1))

    assert output.net_flow_cents == 12000  # 10000 + 5000 - 3000
    assert output.total_cash_movements_cents == 0


def test_cash_flow_isolation_between_companies_integration(session: Session) -> None:
    """Isolamento multiempresa no cálculo do fluxo de caixa."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    now = datetime.now(UTC)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Empresa 1: venda de 100,00
    repo.add(_make_entry("sale", 10000, company_id=1))
    # Empresa 2: venda de 50,00
    repo.add(_make_entry("sale", 5000, company_id=2))
    session.commit()

    output_1 = GetCashFlow(repo).execute(
        CashFlowInput(start_date=start, end_date=end, company_id=1)
    )
    output_2 = GetCashFlow(repo).execute(
        CashFlowInput(start_date=start, end_date=end, company_id=2)
    )

    assert output_1.total_sales_cents == 10000
    assert output_1.net_flow_cents == 10000
    assert output_2.total_sales_cents == 5000
    assert output_2.net_flow_cents == 5000


def test_cash_flow_daily_breakdown_includes_sangria(session: Session) -> None:
    """O breakdown diário deve incluir sangrias no net do dia."""
    repo = SqlAlchemyFinancialEntryRepository(session)

    now = datetime.now(UTC)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Venda de +100,00 hoje
    repo.add(_make_entry("sale", 10000, company_id=1, days_ago=0))
    # Sangria de -30,00 hoje
    repo.add(_make_entry("cash_sangria", -3000, company_id=1, days_ago=0))
    session.commit()

    output = GetCashFlow(repo).execute(CashFlowInput(start_date=start, end_date=end, company_id=1))

    assert len(output.daily_breakdown) == 1
    day = output.daily_breakdown[0]
    assert day["sales_cents"] == 10000
    assert day["cash_movements_cents"] == -3000
    assert day["net_cents"] == 7000  # 10000 - 3000
