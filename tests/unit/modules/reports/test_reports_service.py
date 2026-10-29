"""Unit tests for Reports module."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from erp.modules.reports.application.ports import (
    ReportExporterPort,
    ReportGeneratorPort,
    ReportRepositoryPort,
)
from erp.modules.reports.application.service import (
    ReportService,
    create_report_service,
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

if TYPE_CHECKING:
    pass


class FakeReportGenerator(ReportGeneratorPort):
    def generate_sales_by_period(self, filter_: ReportFilter) -> list[SalesByPeriodRow]:
        return [
            SalesByPeriodRow(
                date=datetime(2026, 1, 1, tzinfo=UTC),
                total_sales=Decimal("1000.00"),
                total_items=10,
                total_transactions=5,
            )
        ]

    def generate_sales_by_product(self, filter_: ReportFilter) -> list[SalesByProductRow]:
        return [
            SalesByProductRow(
                product_id=1,
                product_name="Produto A",
                sku="A-001",
                quantity_sold=5,
                total_revenue=Decimal("500.00"),
                avg_price=Decimal("100.00"),
            )
        ]

    def generate_sales_by_operator(self, filter_: ReportFilter) -> list[SalesByOperatorRow]:
        return [
            SalesByOperatorRow(
                operator_id=1,
                operator_name="João",
                total_sales=Decimal("300.00"),
                total_transactions=3,
                avg_ticket=Decimal("100.00"),
            )
        ]

    def generate_low_stock(self, filter_: ReportFilter) -> list[LowStockRow]:
        return [
            LowStockRow(
                product_id=1,
                product_name="Produto A",
                sku="A-001",
                current_stock=5,
                min_stock=10,
                category_name="Categoria A",
            )
        ]

    def generate_profit_margin(self, filter_: ReportFilter) -> list[ProfitMarginRow]:
        return [
            ProfitMarginRow(
                product_id=1,
                product_name="Produto A",
                sku="A-001",
                cost_price=Decimal("50.00"),
                sale_price=Decimal("100.00"),
                margin_amount=Decimal("50.00"),
                margin_percent=Decimal("50.00"),
            )
        ]

    def generate_simple_dre(self, filter_: ReportFilter) -> list[SimpleDRERow]:
        return [
            SimpleDRERow(category="receita", description="Vendas", amount=Decimal("1000.00")),
            SimpleDRERow(category="despesa", description="Despesas", amount=Decimal("400.00")),
            SimpleDRERow(category="lucro", description="Lucro Líquido", amount=Decimal("600.00")),
        ]

    def generate_cash_closing(self, filter_: ReportFilter) -> list[CashClosingRow]:
        return [
            CashClosingRow(
                session_id=1,
                opened_at=datetime(2026, 1, 1, 8, 0, 0, tzinfo=UTC),
                closed_at=datetime(2026, 1, 1, 18, 0, 0, tzinfo=UTC),
                operator_name="João",
                opening_amount=Decimal("100.00"),
                expected_amount=Decimal("500.00"),
                actual_amount=Decimal("480.00"),
                difference=Decimal("-20.00"),
                sangrias=Decimal("20.00"),
                suprimentos=Decimal("0.00"),
            )
        ]


class FakeReportRepository(ReportRepositoryPort):
    def __init__(self) -> None:
        self._reports: dict[int, Report] = {}
        self._next_id = 1

    def add(self, report: Report) -> None:
        report.id = self._next_id
        self._next_id += 1
        self._reports[report.id] = report

    def get_by_id(self, report_id: int) -> Report | None:
        return self._reports.get(report_id)

    def list_recent(self, limit: int = 50) -> list[Report]:
        return list(self._reports.values())[:limit]


class FakeReportExporter(ReportExporterPort):
    def __init__(self) -> None:
        self.exported: list[tuple[str, str]] = []

    def export_csv(self, rows: list[object], headers: list[str], file_path: str) -> None:
        Path(file_path).write_text("header1,header2\nvalue1,value2\n", encoding="utf-8")
        self.exported.append(("csv", file_path))

    def export_pdf(
        self,
        rows: list[object],
        headers: list[str],
        file_path: str,
        title: str,
        subtitle: str = "",
    ) -> None:
        Path(file_path).write_bytes(b"%PDF-1.4 fake pdf content")
        self.exported.append(("pdf", file_path))


def _make_filter(company_id: int = 1) -> ReportFilter:
    return ReportFilter(
        company_id=company_id,
        start_date=datetime(2026, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 1, 31, tzinfo=UTC),
    )


def test_generate_sales_by_period_report(tmp_path: Path) -> None:
    generator = FakeReportGenerator()
    exporter = FakeReportExporter()
    repo = FakeReportRepository()
    service = ReportService(generator, exporter, repo, tmp_path)

    report = service.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "report.csv"),
        user_id=1,
    )

    assert report.id == 1
    assert report.report_type == ReportType.SALES_BY_PERIOD
    assert report.status == "completed"
    assert report.file_path == str(tmp_path / "report.csv")
    assert report.file_format == ExportFormat.CSV
    assert report.file_size_bytes > 0
    assert report.generated_by_user_id == 1


def test_generate_csv_export(tmp_path: Path) -> None:
    generator = FakeReportGenerator()
    exporter = FakeReportExporter()
    repo = FakeReportRepository()
    service = ReportService(generator, exporter, repo, tmp_path)

    service.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "report.csv"),
    )

    assert len(exporter.exported) == 1
    assert exporter.exported[0][0] == "csv"
    assert exporter.exported[0][1] == str(tmp_path / "report.csv")


def test_generate_pdf_export(tmp_path: Path) -> None:
    generator = FakeReportGenerator()
    exporter = FakeReportExporter()
    repo = FakeReportRepository()
    service = ReportService(generator, exporter, repo, tmp_path)

    service.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(),
        export_format=ExportFormat.PDF,
        file_path=str(tmp_path / "report.pdf"),
    )

    assert len(exporter.exported) == 1
    assert exporter.exported[0][0] == "pdf"


def test_report_repository_crud(tmp_path: Path) -> None:
    repo = FakeReportRepository()

    report = Report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_params={"company_id": 1},
        file_path="/tmp/report.csv",
        file_format="csv",
        generated_by_user_id=1,
    )
    repo.add(report)
    assert report.id == 1

    saved = repo.get_by_id(1)
    assert saved is not None
    assert saved.report_type == ReportType.SALES_BY_PERIOD
    assert saved.status == "pending"

    recent = repo.list_recent()
    assert len(recent) == 1


def test_report_isolation_between_companies(tmp_path: Path) -> None:
    """Reports should be scoped by company_id in filter_params."""
    generator = FakeReportGenerator()
    exporter = FakeReportExporter()
    repo = FakeReportRepository()
    service = ReportService(generator, exporter, repo, tmp_path)

    service.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(company_id=1),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "report1.csv"),
    )
    service.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(company_id=2),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "report2.csv"),
    )

    recent = repo.list_recent()
    assert len(recent) == 2
    assert recent[0].filter_params["company_id"] == 1
    assert recent[1].filter_params["company_id"] == 2


def test_create_report_service_factory(tmp_path: Path) -> None:
    generator = FakeReportGenerator()
    repo = FakeReportRepository()
    service = create_report_service(generator, repo, tmp_path)

    assert isinstance(service, ReportService)
    assert service._reports_dir == tmp_path


def test_all_report_types(tmp_path: Path) -> None:
    generator = FakeReportGenerator()
    exporter = FakeReportExporter()
    repo = FakeReportRepository()
    service = ReportService(generator, exporter, repo, tmp_path)

    report_types = [
        ReportType.SALES_BY_PERIOD,
        ReportType.SALES_BY_PRODUCT,
        ReportType.SALES_BY_OPERATOR,
        ReportType.LOW_STOCK,
        ReportType.PROFIT_MARGIN,
        ReportType.SIMPLE_DRE,
        ReportType.CASH_CLOSING,
    ]

    for rtype in report_types:
        report = service.generate_report(
            report_type=rtype,
            filter_=_make_filter(),
            export_format=ExportFormat.CSV,
            file_path=str(tmp_path / f"{rtype}.csv"),
        )
        assert report.status == "completed"
        assert report.file_path.endswith(f"{rtype}.csv")


def test_report_filter_for_period() -> None:
    filter_ = ReportFilter.for_period(
        company_id=1,
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 31, tzinfo=UTC),
    )
    assert filter_.company_id == 1
    assert filter_.start_date == datetime(2026, 1, 1, tzinfo=UTC)
    assert filter_.end_date == datetime(2026, 1, 31, tzinfo=UTC)
