"""Unit tests for GetCashFlow use case."""

from __future__ import annotations

from datetime import UTC, datetime

from erp.modules.treasury.application.get_cash_flow import (
    CashFlowInput,
    GetCashFlow,
)
from erp.modules.treasury.domain.financial_entry import FinancialEntry


class FakeFinancialEntryRepository:
    def __init__(self) -> None:
        self._entries: list[FinancialEntry] = []

    def add(self, entry: FinancialEntry) -> None:
        self._entries.append(entry)

    def list_by_company(self, company_id: int | None = None) -> list[FinancialEntry]:
        if company_id is None:
            return list(self._entries)
        return [e for e in self._entries if e.company_id == company_id]

    def list_by_period(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
    ) -> list[FinancialEntry]:
        result = []
        for e in self._entries:
            if e.date is None:
                continue
            if e.date < start_date or e.date > end_date:
                continue
            if company_id is not None and e.company_id != company_id:
                continue
            result.append(e)
        return result


def _make_entry(
    type_: str,
    amount_cents: int,
    company_id: int = 1,
    days_ago: int = 0,
) -> FinancialEntry:
    from datetime import timedelta

    return FinancialEntry(
        company_id=company_id,
        type=type_,
        amount_cents=amount_cents,
        source_type="sale",
        source_id=1,
        description="teste",
        date=datetime.now(UTC) - timedelta(days=days_ago),
    )


def test_get_cash_flow_basic() -> None:
    repo = FakeFinancialEntryRepository()
    repo.add(_make_entry("sale", 10000, company_id=1))
    repo.add(_make_entry("receivable", 5000, company_id=1))
    repo.add(_make_entry("payable", 3000, company_id=1))

    now = datetime.now(UTC)
    output = GetCashFlow(repo).execute(
        CashFlowInput(
            start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            company_id=1,
        )
    )
    assert output.total_sales_cents == 10000
    assert output.total_receivables_cents == 5000
    assert output.total_payables_cents == 3000
    assert output.net_flow_cents == 12000  # 10000 + 5000 - 3000


def test_get_cash_flow_isolation_between_companies() -> None:
    repo = FakeFinancialEntryRepository()
    repo.add(_make_entry("sale", 10000, company_id=1))
    repo.add(_make_entry("sale", 20000, company_id=2))

    now = datetime.now(UTC)
    output_1 = GetCashFlow(repo).execute(
        CashFlowInput(
            start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            company_id=1,
        )
    )
    output_2 = GetCashFlow(repo).execute(
        CashFlowInput(
            start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            company_id=2,
        )
    )
    assert output_1.total_sales_cents == 10000
    assert output_2.total_sales_cents == 20000


def test_get_cash_flow_reconciliation_with_sangria() -> None:
    """Reconciliação: fluxo = vendas + recebíveis - pagáveis - sangrias no período."""
    repo = FakeFinancialEntryRepository()
    repo.add(_make_entry("sale", 10000, company_id=1))  # +100,00
    repo.add(_make_entry("receivable", 5000, company_id=1))  # +50,00
    repo.add(_make_entry("payable", 3000, company_id=1))  # -30,00
    repo.add(_make_entry("cash_sangria", -2000, company_id=1))  # -20,00 (sangria)
    repo.add(_make_entry("cash_suprimento", 1000, company_id=1))  # +10,00 (suprimento)

    now = datetime.now(UTC)
    output = GetCashFlow(repo).execute(
        CashFlowInput(
            start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=now.replace(hour=23, minute=59, second=59, microsecond=999999),
            company_id=1,
        )
    )
    # net = 10000 + 5000 - 3000 + (-2000) + 1000 = 11000
    assert output.total_sales_cents == 10000
    assert output.total_receivables_cents == 5000
    assert output.total_payables_cents == 3000
    assert output.total_cash_movements_cents == -1000  # -2000 + 1000
    assert output.net_flow_cents == 11000  # 10000 + 5000 - 3000 + (-1000)
