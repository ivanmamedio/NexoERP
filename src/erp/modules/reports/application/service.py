"""Report generation and export service."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from erp.modules.reports.application.ports import (
    ReportExporterPort,
    ReportGeneratorPort,
    ReportRepositoryPort,
    ReportServicePort,
)
from erp.modules.reports.domain import (
    ExportFormat,
    Report,
    ReportFilter,
    ReportType,
)

if TYPE_CHECKING:
    pass


class ReportService(ReportServicePort):
    """Service for generating and exporting reports."""

    def __init__(
        self,
        generator: ReportGeneratorPort,
        exporter: ReportExporterPort,
        repository: ReportRepositoryPort,
        reports_dir: Path,
    ) -> None:
        self._generator = generator
        self._exporter = exporter
        self._repository = repository
        self._reports_dir = reports_dir
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        report_type: str,
        filter_: ReportFilter,
        export_format: str,
        file_path: str,
        user_id: int | None = None,
    ) -> Report:
        report = Report(
            report_type=report_type,
            filter_params={
                "company_id": filter_.company_id,
                "start_date": filter_.start_date.isoformat() if filter_.start_date else None,
                "end_date": filter_.end_date.isoformat() if filter_.end_date else None,
                "product_id": filter_.product_id,
                "operator_id": filter_.operator_id,
                "category_id": filter_.category_id,
            },
            file_path=file_path,
            file_format=export_format,
            generated_by_user_id=user_id,
            status="pending",
        )

        try:
            rows = self._generate_rows(report_type, filter_)
            headers = self._get_headers(report_type)

            if export_format == ExportFormat.CSV:
                self._exporter.export_csv(rows, headers, file_path)
            elif export_format == ExportFormat.PDF:
                title = self._get_title(report_type)
                subtitle = self._get_subtitle(filter_)
                self._exporter.export_pdf(rows, headers, file_path, title, subtitle)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            file_size = Path(file_path).stat().st_size
            report.mark_completed(file_path, file_size)

        except Exception as exc:
            report.mark_failed(str(exc))
            raise

        self._repository.add(report)
        return report

    def _generate_rows(self, report_type: str, filter_: ReportFilter) -> list[object]:
        if report_type == ReportType.SALES_BY_PERIOD:
            return list(self._generator.generate_sales_by_period(filter_))
        elif report_type == ReportType.SALES_BY_PRODUCT:
            return list(self._generator.generate_sales_by_product(filter_))
        elif report_type == ReportType.SALES_BY_OPERATOR:
            return list(self._generator.generate_sales_by_operator(filter_))
        elif report_type == ReportType.LOW_STOCK:
            return list(self._generator.generate_low_stock(filter_))
        elif report_type == ReportType.PROFIT_MARGIN:
            return list(self._generator.generate_profit_margin(filter_))
        elif report_type == ReportType.SIMPLE_DRE:
            return list(self._generator.generate_simple_dre(filter_))
        elif report_type == ReportType.CASH_CLOSING:
            return list(self._generator.generate_cash_closing(filter_))
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def _get_headers(self, report_type: str) -> list[str]:
        headers_map: dict[str, list[str]] = {
            ReportType.SALES_BY_PERIOD: [
                "Data",
                "Total Vendas",
                "Total Itens",
                "Total Transações",
            ],
            ReportType.SALES_BY_PRODUCT: [
                "ID Produto",
                "Nome",
                "SKU",
                "Qtd Vendida",
                "Receita Total",
                "Preço Médio",
            ],
            ReportType.SALES_BY_OPERATOR: [
                "ID Operador",
                "Nome",
                "Total Vendas",
                "Total Transações",
                "Ticket Médio",
            ],
            ReportType.LOW_STOCK: [
                "ID Produto",
                "Nome",
                "SKU",
                "Estoque Atual",
                "Estoque Mínimo",
                "Categoria",
            ],
            ReportType.PROFIT_MARGIN: [
                "ID Produto",
                "Nome",
                "SKU",
                "Preço Custo",
                "Preço Venda",
                "Margem (R$)",
                "Margem (%)",
            ],
            ReportType.SIMPLE_DRE: [
                "Categoria",
                "Descrição",
                "Valor",
            ],
            ReportType.CASH_CLOSING: [
                "ID Sessão",
                "Abertura",
                "Fechamento",
                "Operador",
                "Valor Inicial",
                "Valor Esperado",
                "Valor Real",
                "Diferença",
                "Sangrias",
                "Suprimentos",
            ],
        }
        return headers_map.get(report_type, [])

    def _get_title(self, report_type: str) -> str:
        titles: dict[str, str] = {
            ReportType.SALES_BY_PERIOD: "Vendas por Período",
            ReportType.SALES_BY_PRODUCT: "Vendas por Produto",
            ReportType.SALES_BY_OPERATOR: "Vendas por Operador",
            ReportType.LOW_STOCK: "Estoque Baixo",
            ReportType.PROFIT_MARGIN: "Margem de Lucro",
            ReportType.SIMPLE_DRE: "DRE Simplificado",
            ReportType.CASH_CLOSING: "Fechamento de Caixa",
        }
        return titles.get(report_type, "Relatório")

    def _get_subtitle(self, filter_: ReportFilter) -> str:
        parts = []
        if filter_.start_date and filter_.end_date:
            start = filter_.start_date.strftime("%d/%m/%Y")
            end = filter_.end_date.strftime("%d/%m/%Y")
            parts.append(f"Período: {start} a {end}")
        elif filter_.start_date:
            parts.append(f"Desde: {filter_.start_date.strftime('%d/%m/%Y')}")
        elif filter_.end_date:
            parts.append(f"Até: {filter_.end_date.strftime('%d/%m/%Y')}")

        return " | ".join(parts)


class CSVExporter(ReportExporterPort):
    """CSV exporter implementation."""

    def export_csv(self, rows: list[object], headers: list[str], file_path: str) -> None:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            for row in rows:
                writer.writerow(self._row_to_list(row))

    def export_pdf(
        self,
        rows: list[object],
        headers: list[str],
        file_path: str,
        title: str,
        subtitle: str = "",
    ) -> None:
        # Lazy import for PDF
        self._export_pdf_lazy(rows, headers, file_path, title, subtitle)

    def _row_to_list(self, row: object) -> list[str]:
        if hasattr(row, "__dataclass_fields__"):
            return [str(getattr(row, field.name)) for field in row.__dataclass_fields__.values()]
        elif hasattr(row, "__dict__"):
            return [str(v) for v in row.__dict__.values()]
        return [str(row)]

    def _export_pdf_lazy(
        self,
        rows: list[object],
        headers: list[str],
        file_path: str,
        title: str,
        subtitle: str = "",
    ) -> None:
        # Import reportlab lazily
        from reportlab.lib import colors  # type: ignore[import-untyped]
        from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
        from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
        from reportlab.lib.units import cm  # type: ignore[import-untyped]
        from reportlab.platypus import (  # type: ignore[import-untyped]
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        doc = SimpleDocTemplate(
            file_path,
            pagesize=landscape(A4),
            leftMargin=1 * cm,
            rightMargin=1 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(title, styles["Title"]))
        if subtitle:
            story.append(Paragraph(subtitle, styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

        # Table
        data = [headers]
        for row in rows:
            data.append(self._row_to_list(row))

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        story.append(table)
        doc.build(story)


def create_report_service(
    generator: ReportGeneratorPort,
    repository: ReportRepositoryPort,
    reports_dir: Path,
) -> ReportService:
    exporter = CSVExporter()
    return ReportService(generator, exporter, repository, reports_dir)
