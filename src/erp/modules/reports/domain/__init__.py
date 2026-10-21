"""Reports domain entities and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from erp.shared.domain.entities import Entity


class ReportType(StrEnum):
    SALES_BY_PERIOD = "sales_by_period"
    SALES_BY_PRODUCT = "sales_by_product"
    SALES_BY_OPERATOR = "sales_by_operator"
    LOW_STOCK = "low_stock"
    PROFIT_MARGIN = "profit_margin"
    SIMPLE_DRE = "simple_dre"
    CASH_CLOSING = "cash_closing"


class ExportFormat(StrEnum):
    CSV = "csv"
    PDF = "pdf"


@dataclass(slots=True)
class ReportFilter:
    """Filter parameters for reports."""

    company_id: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    product_id: int | None = None
    operator_id: int | None = None
    category_id: int | None = None

    @staticmethod
    def for_period(company_id: int, start: datetime, end: datetime) -> ReportFilter:
        return ReportFilter(company_id=company_id, start_date=start, end_date=end)


@dataclass(slots=True)
class SalesByPeriodRow:
    """Row for sales by period report."""

    date: datetime
    total_sales: Decimal
    total_items: int
    total_transactions: int


@dataclass(slots=True)
class SalesByProductRow:
    """Row for sales by product report."""

    product_id: int
    product_name: str
    sku: str
    quantity_sold: int
    total_revenue: Decimal
    avg_price: Decimal


@dataclass(slots=True)
class SalesByOperatorRow:
    """Row for sales by operator report."""

    operator_id: int
    operator_name: str
    total_sales: Decimal
    total_transactions: int
    avg_ticket: Decimal


@dataclass(slots=True)
class LowStockRow:
    """Row for low stock report."""

    product_id: int
    product_name: str
    sku: str
    current_stock: int
    min_stock: int
    category_name: str


@dataclass(slots=True)
class ProfitMarginRow:
    """Row for profit margin report."""

    product_id: int
    product_name: str
    sku: str
    cost_price: Decimal
    sale_price: Decimal
    margin_amount: Decimal
    margin_percent: Decimal


@dataclass(slots=True)
class SimpleDRERow:
    """Row for simple DRE report."""

    category: str  # revenue, expense, profit
    description: str
    amount: Decimal


@dataclass(slots=True)
class CashClosingRow:
    """Row for cash closing report."""

    session_id: int
    opened_at: datetime
    closed_at: datetime | None
    operator_name: str
    opening_amount: Decimal
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    sangrias: Decimal
    suprimentos: Decimal


@dataclass(slots=True)
class Report(Entity):
    """Report entity with metadata."""

    report_type: str = ""
    filter_params: dict[str, str | int | None] = field(default_factory=dict)
    file_path: str = ""
    file_format: str = ""
    file_size_bytes: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    generated_by_user_id: int | None = None
    status: str = "pending"  # pending, completed, failed
    error_message: str = ""

    def mark_completed(self, file_path: str, file_size: int) -> None:
        self.status = "completed"
        self.file_path = file_path
        self.file_size_bytes = file_size

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error_message = error
