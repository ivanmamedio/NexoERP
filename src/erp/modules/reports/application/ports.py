"""Application ports for the reports module."""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from erp.modules.reports.domain import (
    CashClosingRow,
    LowStockRow,
    ProfitMarginRow,
    Report,
    ReportFilter,
    SalesByOperatorRow,
    SalesByPeriodRow,
    SalesByProductRow,
    SimpleDRERow,
)


@runtime_checkable
class ReportRepositoryPort(Protocol):
    @abstractmethod
    def add(self, report: Report) -> None: ...

    @abstractmethod
    def get_by_id(self, report_id: int) -> Report | None: ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[Report]: ...


@runtime_checkable
class ReportGeneratorPort(Protocol):
    @abstractmethod
    def generate_sales_by_period(self, filter_: ReportFilter) -> list[SalesByPeriodRow]: ...

    @abstractmethod
    def generate_sales_by_product(self, filter_: ReportFilter) -> list[SalesByProductRow]: ...

    @abstractmethod
    def generate_sales_by_operator(self, filter_: ReportFilter) -> list[SalesByOperatorRow]: ...

    @abstractmethod
    def generate_low_stock(self, filter_: ReportFilter) -> list[LowStockRow]: ...

    @abstractmethod
    def generate_profit_margin(self, filter_: ReportFilter) -> list[ProfitMarginRow]: ...

    @abstractmethod
    def generate_simple_dre(self, filter_: ReportFilter) -> list[SimpleDRERow]: ...

    @abstractmethod
    def generate_cash_closing(self, filter_: ReportFilter) -> list[CashClosingRow]: ...


@runtime_checkable
class ReportExporterPort(Protocol):
    @abstractmethod
    def export_csv(self, rows: list[object], headers: list[str], file_path: str) -> None: ...

    @abstractmethod
    def export_pdf(
        self,
        rows: list[object],
        headers: list[str],
        file_path: str,
        title: str,
        subtitle: str = "",
    ) -> None: ...


@runtime_checkable
class ReportServicePort(Protocol):
    @abstractmethod
    def generate_report(
        self,
        report_type: str,
        filter_: ReportFilter,
        export_format: str,
        file_path: str,
        user_id: int | None = None,
    ) -> Report: ...
