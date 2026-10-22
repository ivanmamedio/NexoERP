"""Integration tests for Reports module using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from erp.modules.reports.application.ports import ReportGeneratorPort
from erp.modules.reports.application.service import CSVExporter, ReportService
from erp.modules.reports.domain import (
    ExportFormat,
    Report,
    ReportFilter,
    ReportType,
)
from erp.modules.reports.infrastructure.generator import SqlReportGenerator
from erp.modules.reports.infrastructure.models import Base
from erp.modules.reports.infrastructure.repository import (
    SqlAlchemyReportRepository,
)


@pytest.fixture()
def session(tmp_path: Path) -> Generator[Session, None, None]:
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)

    # Criar tabelas necessárias para os geradores de relatório
    with Session(engine) as setup_session:
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    operator_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'draft',
                    created_at DATETIME NOT NULL
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity REAL NOT NULL DEFAULT 0,
                    total_price REAL NOT NULL DEFAULT 0
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    sku VARCHAR(100) NOT NULL,
                    cost_price REAL NOT NULL DEFAULT 0,
                    sale_price REAL NOT NULL DEFAULT 0,
                    min_stock INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    category_id INTEGER
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS cash_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    operator_id INTEGER NOT NULL,
                    opening_amount REAL NOT NULL DEFAULT 0,
                    expected_amount REAL NOT NULL DEFAULT 0,
                    closing_amount REAL NOT NULL DEFAULT 0,
                    opened_at DATETIME NOT NULL,
                    closed_at DATETIME
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS cash_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    amount REAL NOT NULL DEFAULT 0
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS financial_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS payables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    category_id INTEGER,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending'
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS payable_installments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payable_id INTEGER NOT NULL,
                    amount REAL NOT NULL DEFAULT 0,
                    due_date DATETIME NOT NULL
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,
                    quantity REAL NOT NULL DEFAULT 0
                )
            """
            )
        )
        setup_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    name VARCHAR(200) NOT NULL
                )
            """
            )
        )
        setup_session.commit()

    session = Session(engine)
    yield session
    session.close()


def _make_filter(company_id: int = 1) -> ReportFilter:
    return ReportFilter(
        company_id=company_id,
        start_date=datetime(2026, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 1, 31, tzinfo=UTC),
    )


def test_report_crud(session: Session) -> None:
    repo = SqlAlchemyReportRepository(session)

    report = Report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_params={"company_id": 1},
        file_path="/tmp/report.csv",
        file_format="csv",
        generated_by_user_id=1,
    )
    repo.add(report)
    assert report.id is not None

    saved = repo.get_by_id(report.id or 0)
    assert saved is not None
    assert saved.report_type == ReportType.SALES_BY_PERIOD
    assert saved.file_path == "/tmp/report.csv"

    recent = repo.list_recent()
    assert len(recent) == 1


def test_sql_report_generator_sales_by_period(session: Session) -> None:
    generator = SqlReportGenerator(session)

    session.execute(
        text(
            "INSERT INTO sales (company_id, operator_id, total_amount, status, created_at) "
            "VALUES (1, 1, 1000.00, 'finalized', '2026-01-15 10:00:00')"
        )
    )
    session.execute(
        text(
            "INSERT INTO sales (company_id, operator_id, total_amount, status, created_at) "
            "VALUES (1, 1, 500.00, 'finalized', '2026-01-20 14:00:00')"
        )
    )
    session.commit()

    rows = generator.generate_sales_by_period(_make_filter(company_id=1))
    assert len(rows) == 2  # Dois dias diferentes
    assert rows[0].total_sales > 0


def test_sql_report_generator_low_stock(session: Session) -> None:
    generator = SqlReportGenerator(session)

    session.execute(
        text(
            "INSERT INTO products (company_id, name, sku, min_stock, active, "
            "cost_price, sale_price) VALUES (1, 'Produto Teste', 'TEST-001', "
            "10, 1, 50.00, 100.00)"
        )
    )
    session.commit()

    rows = generator.generate_low_stock(_make_filter(company_id=1))
    assert len(rows) >= 1  # Sem tabela inventory, estoque = 0 <= min_stock 10


def test_sql_report_generator_profit_margin(session: Session) -> None:
    generator = SqlReportGenerator(session)

    session.execute(
        text(
            "INSERT INTO products (company_id, name, sku, cost_price, sale_price, active) "
            "VALUES (1, 'Produto Teste', 'TEST-001', 50.00, 100.00, 1)"
        )
    )
    session.commit()

    rows = generator.generate_profit_margin(_make_filter(company_id=1))
    assert len(rows) == 1
    assert rows[0].product_name == "Produto Teste"
    assert rows[0].cost_price == Decimal("50.00")
    assert rows[0].sale_price == Decimal("100.00")
    assert rows[0].margin_amount == Decimal("50.00")


class FakeGenerator(ReportGeneratorPort):
    def generate_sales_by_period(self, filter_):
        return []

    def generate_sales_by_product(self, filter_):
        return []

    def generate_sales_by_operator(self, filter_):
        return []

    def generate_low_stock(self, filter_):
        return []

    def generate_profit_margin(self, filter_):
        return []

    def generate_simple_dre(self, filter_):
        return []

    def generate_cash_closing(self, filter_):
        return []


def test_csv_export(tmp_path: Path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = SqlAlchemyReportRepository(Session(engine))

    service = ReportService(
        generator=FakeGenerator(),
        exporter=CSVExporter(),
        repository=repo,
        reports_dir=tmp_path,
    )

    report = service.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "test_report.csv"),
        user_id=1,
    )

    assert report.status == "completed"
    assert report.file_path.endswith(".csv")
    assert Path(report.file_path).exists()

    content = Path(report.file_path).read_text(encoding="utf-8")
    assert "Data" in content
    assert "Total Vendas" in content


def test_report_isolation_between_companies(tmp_path: Path) -> None:
    engine1 = create_engine("sqlite:///:memory:")
    engine2 = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine1)
    Base.metadata.create_all(engine2)

    repo1 = SqlAlchemyReportRepository(Session(engine1))
    repo2 = SqlAlchemyReportRepository(Session(engine2))

    service1 = ReportService(
        generator=FakeGenerator(),
        exporter=CSVExporter(),
        repository=repo1,
        reports_dir=tmp_path / "reports1",
    )
    service2 = ReportService(
        generator=FakeGenerator(),
        exporter=CSVExporter(),
        repository=repo2,
        reports_dir=tmp_path / "reports2",
    )

    service1.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(company_id=1),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "r1.csv"),
    )
    service2.generate_report(
        report_type=ReportType.SALES_BY_PERIOD,
        filter_=_make_filter(company_id=2),
        export_format=ExportFormat.CSV,
        file_path=str(tmp_path / "r2.csv"),
    )

    recent1 = repo1.list_recent()
    recent2 = repo2.list_recent()

    assert len(recent1) == 1
    assert len(recent2) == 1
    assert recent1[0].filter_params["company_id"] == 1
    assert recent2[0].filter_params["company_id"] == 2
