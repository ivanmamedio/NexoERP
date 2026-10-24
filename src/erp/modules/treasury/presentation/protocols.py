"""Shared protocols for Treasury presentation layer."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from erp.modules.treasury.application.get_cash_flow import CashFlowOutput
from erp.modules.treasury.application.get_category_summary import GetCategorySummaryOutput
from erp.modules.treasury.application.get_payables_due_soon import GetPayablesDueSoonOutput
from erp.modules.treasury.application.get_receivables_due_soon import GetReceivablesDueSoonOutput
from erp.modules.treasury.application.list_payables_by_due_date import ListPayablesByDueDateOutput
from erp.modules.treasury.application.list_receivables_by_due_date import (
    ListReceivablesByDueDateOutput,
)


@runtime_checkable
class TreasuryDashboardView(Protocol):
    """Contrato da tela principal de tesouraria."""

    def show_error(self, message: str) -> None: ...
    def set_cash_flow(self, output: CashFlowOutput) -> None: ...
    def set_payables(self, output: ListPayablesByDueDateOutput) -> None: ...
    def set_receivables(self, output: ListReceivablesByDueDateOutput) -> None: ...
    def set_alerts(
        self,
        payables_output: GetPayablesDueSoonOutput,
        receivables_output: GetReceivablesDueSoonOutput,
    ) -> None: ...
    def set_category_summary(self, output: GetCategorySummaryOutput) -> None: ...
    def get_start_date(self) -> datetime: ...
    def get_end_date(self) -> datetime: ...
    def get_days_ahead(self) -> int: ...
    def accept(self) -> None: ...
