"""GetCashFlow use case — fluxo de caixa por período."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from itertools import groupby
from typing import Any, TypedDict

from erp.modules.treasury.application.ports import FinancialEntryRepository


@dataclass(slots=True, frozen=True)
class CashFlowInput:
    start_date: datetime
    end_date: datetime
    company_id: int | None = None


class DailyBreakdownItem(TypedDict):
    date: date
    sales_cents: int
    receivables_cents: int
    payables_cents: int
    cash_movements_cents: int
    net_cents: int


class MonthlyBreakdownItem(TypedDict):
    month: date
    sales_cents: int
    receivables_cents: int
    payables_cents: int
    cash_movements_cents: int
    net_cents: int


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
    daily_breakdown: list[DailyBreakdownItem]
    monthly_breakdown: list[MonthlyBreakdownItem]


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
            elif entry.type in (
                "cash_opening",
                "cash_sangria",
                "cash_suprimento",
                "cash_closing",
            ):
                total_cash += entry.amount_cents

        net_flow = total_sales + total_receivables - total_payables

        # Agrupar por dia
        daily_data = self._group_by_day(entries)
        # Agrupar por mês
        monthly_data = self._group_by_month(entries)

        return CashFlowOutput(
            start_date=input.start_date,
            end_date=input.end_date,
            company_id=input.company_id,
            total_sales_cents=total_sales,
            total_receivables_cents=total_receivables,
            total_payables_cents=total_payables,
            total_cash_movements_cents=total_cash,
            net_flow_cents=net_flow,
            daily_breakdown=daily_data,
            monthly_breakdown=monthly_data,
        )

    def _group_by_day(self, entries: list[Any]) -> list[DailyBreakdownItem]:
        """Agrupa entradas por dia."""
        # Ordenar por data
        entries_with_date = [e for e in entries if e.date is not None]
        entries_with_date.sort(key=lambda x: x.date)

        daily: list[DailyBreakdownItem] = []
        for day, group in groupby(entries_with_date, key=lambda x: x.date.date()):
            day_sales = 0
            day_receivables = 0
            day_payables = 0
            day_cash = 0

            for entry in group:
                if entry.type == "sale":
                    day_sales += entry.amount_cents
                elif entry.type == "receivable":
                    day_receivables += entry.amount_cents
                elif entry.type == "payable":
                    day_payables += entry.amount_cents
                elif entry.type in (
                    "cash_opening",
                    "cash_sangria",
                    "cash_suprimento",
                    "cash_closing",
                ):
                    day_cash += entry.amount_cents

            net = day_sales + day_receivables - day_payables
            daily.append(
                DailyBreakdownItem(
                    date=day,
                    sales_cents=day_sales,
                    receivables_cents=day_receivables,
                    payables_cents=day_payables,
                    cash_movements_cents=day_cash,
                    net_cents=net,
                )
            )

        return daily

    def _group_by_month(self, entries: list[Any]) -> list[MonthlyBreakdownItem]:
        """Agrupa entradas por mês."""
        entries_with_date = [e for e in entries if e.date is not None]
        entries_with_date.sort(key=lambda x: x.date)

        monthly: list[MonthlyBreakdownItem] = []
        for month, group in groupby(entries_with_date, key=lambda x: (x.date.year, x.date.month)):
            month_sales = 0
            month_receivables = 0
            month_payables = 0
            month_cash = 0

            for entry in group:
                if entry.type == "sale":
                    month_sales += entry.amount_cents
                elif entry.type == "receivable":
                    month_receivables += entry.amount_cents
                elif entry.type == "payable":
                    month_payables += entry.amount_cents
                elif entry.type in (
                    "cash_opening",
                    "cash_sangria",
                    "cash_suprimento",
                    "cash_closing",
                ):
                    month_cash += entry.amount_cents

            net = month_sales + month_receivables - month_payables
            # Usar o primeiro dia do mês como representante
            month_date = date(month[0], month[1], 1)
            monthly.append(
                MonthlyBreakdownItem(
                    month=month_date,
                    sales_cents=month_sales,
                    receivables_cents=month_receivables,
                    payables_cents=month_payables,
                    cash_movements_cents=month_cash,
                    net_cents=net,
                )
            )

        return monthly
