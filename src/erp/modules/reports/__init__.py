"""Reports module - sales, inventory, margin, DRE, cash closing reports."""

from erp.modules.reports.application import (
    ReportExporterPort,
    ReportGeneratorPort,
    ReportRepositoryPort,
    ReportService,
    ReportServicePort,
)
from erp.modules.reports.domain import (
    CashClosingRow,
    ExportFormat,
    LowStockRow,
    ProfitMarginRow,
    Report,
    ReportFilter,
    ReportType,
    SalesByOperatorRow,
    SalesByPeriodRow,
    SalesByProductRow,
    SimpleDRERow,
)
from erp.modules.reports.infrastructure import SqlAlchemyReportRepository, SqlReportGenerator
from erp.modules.reports.presentation import ReportDialog

__all__ = [
    "CashClosingRow",
    "ExportFormat",
    "LowStockRow",
    "ProfitMarginRow",
    "Report",
    "ReportDialog",
    "ReportExporterPort",
    "ReportFilter",
    "ReportGeneratorPort",
    "ReportRepositoryPort",
    "ReportService",
    "ReportServicePort",
    "ReportType",
    "SalesByOperatorRow",
    "SalesByPeriodRow",
    "SalesByProductRow",
    "SimpleDRERow",
    "SqlAlchemyReportRepository",
    "SqlReportGenerator",
]
