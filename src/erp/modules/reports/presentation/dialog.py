"""Report generation dialog."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from erp.modules.reports.application.service import ReportService


class ReportDialog(QDialog):
    """Dialog for generating reports."""

    def __init__(
        self,
        report_service: ReportService,
        company_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._report_service = report_service
        self._company_id = company_id

        self.setWindowTitle("Gerar Relatório")
        self.setModal(True)
        self.resize(500, 500)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Report type
        self._type_combo = QComboBox()
        self._type_combo.addItems(
            [
                "Vendas por Período",
                "Vendas por Produto",
                "Vendas por Operador",
                "Estoque Baixo",
                "Margem de Lucro",
                "DRE Simplificado",
                "Fechamento de Caixa",
            ]
        )
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Tipo de Relatório:", self._type_combo)

        # Date range
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate().addMonths(-1))
        form.addRow("Data Inicial:", self._start_date)

        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        form.addRow("Data Final:", self._end_date)

        # Product filter (optional)
        self._product_combo = QComboBox()
        self._product_combo.addItem("Todos", None)
        form.addRow("Produto:", self._product_combo)

        # Operator filter (optional)
        self._operator_combo = QComboBox()
        self._operator_combo.addItem("Todos", None)
        form.addRow("Operador:", self._operator_combo)

        # Category filter (optional)
        self._category_combo = QComboBox()
        self._category_combo.addItem("Todas", None)
        form.addRow("Categoria:", self._category_combo)

        # Export format
        self._format_combo = QComboBox()
        self._format_combo.addItems(["CSV", "PDF"])
        form.addRow("Formato:", self._format_combo)

        # Output file
        self._file_path_edit = QLabel()
        self._file_path_edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Arquivo de Saída:", self._file_path_edit)

        browse_btn = QPushButton("Escolher...")
        browse_btn.clicked.connect(self._browse_file)
        form.addRow("", browse_btn)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        generate_btn = QPushButton("Gerar Relatório")
        generate_btn.setDefault(True)
        generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(generate_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_type_changed(self, text: str) -> None:
        # Show/hide fields based on report type
        is_sales = "Vendas" in text
        is_cash = "Caixa" in text
        is_stock = "Estoque" in text
        is_margin = "Margem" in text

        self._product_combo.setVisible(is_sales or is_margin)
        self._operator_combo.setVisible(is_sales or is_cash)
        self._category_combo.setVisible(is_sales or is_margin or is_stock)

    def _browse_file(self) -> None:
        file_filter = "CSV Files (*.csv);;PDF Files (*.pdf)"
        if self._format_combo.currentText() == "PDF":
            file_filter = "PDF Files (*.pdf);;CSV Files (*.csv)"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            str(Path.home() / "relatorio"),
            file_filter,
        )
        if file_path:
            self._file_path_edit.setText(file_path)

    def _on_generate(self) -> None:
        from erp.modules.reports.domain import ExportFormat, ReportFilter, ReportType

        # Build filter
        type_map = {
            "Vendas por Período": ReportType.SALES_BY_PERIOD,
            "Vendas por Produto": ReportType.SALES_BY_PRODUCT,
            "Vendas por Operador": ReportType.SALES_BY_OPERATOR,
            "Estoque Baixo": ReportType.LOW_STOCK,
            "Margem de Lucro": ReportType.PROFIT_MARGIN,
            "DRE Simplificado": ReportType.SIMPLE_DRE,
            "Fechamento de Caixa": ReportType.CASH_CLOSING,
        }

        report_type = type_map[self._type_combo.currentText()]
        start_qdate = self._start_date.date()
        end_qdate = self._end_date.date()

        # Convert QDate to datetime
        start_dt = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day(), tzinfo=UTC)
        end_dt = datetime(
            end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59, tzinfo=UTC
        )

        product_id = self._product_combo.currentData()
        operator_id = self._operator_combo.currentData()
        category_id = self._category_combo.currentData()

        filter_ = ReportFilter(
            company_id=self._company_id,
            start_date=start_dt,
            end_date=end_dt,
            product_id=product_id,
            operator_id=operator_id,
            category_id=category_id,
        )

        is_csv = self._format_combo.currentText() == "CSV"
        export_format = ExportFormat.CSV if is_csv else ExportFormat.PDF
        file_path = self._file_path_edit.text()

        if not file_path:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo de saída.")
            return

        try:
            report = self._report_service.generate_report(
                report_type=report_type,
                filter_=filter_,
                export_format=export_format,
                file_path=file_path,
            )
            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório gerado com sucesso!\n{report.file_path}",
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {exc}")


def create_report_dialog(
    report_service: ReportService,
    company_id: int,
    parent: QWidget | None = None,
) -> ReportDialog:
    return ReportDialog(report_service, company_id, parent)
