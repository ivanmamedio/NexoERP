"""GetCashFlow use case — fluxo de caixa por período."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from erp.modules.treasury.application.ports import FinancialEntryRepository


@dataclass(slots=True, frozen=True)
class CashFlowInput:
    start_date: datetime
    end_date: datetime
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class CashFlowOutput:
    start_date: datetime
    end_date: datetime
    company_id: int | None
    total_sales_cents: int
    total_receivables_cents: int
    total_payables_cents: int
    total_cash_movements_cents: int
    net_flow_cents: int


class GetCashFlow:
    """Calcula o fluxo de caixa em um período.

    Fluxo = vendas + recebimentos - pagamentos - sangrias no período.
    """

    def __init__(self, repo: FinancialEntryRepository) -> None:
        self._repo = repo

    def execute(self, input: CashFlowInput) -> CashFlowOutput:
        entries = self._repo.list_by_period(
            start_date=input.start_date,
            end_date=input.end_date,
            company_id=input.company_id,
        )

        total_sales = 0
        total_receivables = 0
        total_payables = 0
        total_cash = 0

        for entry in entries:
            if entry.type == "sale":
                total_sales += entry.amount_cents
            elif entry.type == "receivable":
                total_receivables += entry.amount_cents
            elif entry.type == "payable":
                total_payables += entry.amount_cents
            elif entry.type in ("cash_opening", "cash_sangria", "cash_suprimento", "cash_closing"):
                total_cash += entry.amount_cents

        net_flow = total_sales + total_receivables - total_payables

        return CashFlowOutput(
            start_date=input.start_date,
            end_date=input.end_date,
            company_id=input.company_id,
            total_sales_cents=total_sales,
            total_receivables_cents=total_receivables,
            total_payables_cents=total_payables,
            total_cash_movements_cents=total_cash,
            net_flow_cents=net_flow,
        )
