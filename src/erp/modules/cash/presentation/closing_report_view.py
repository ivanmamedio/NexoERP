"""Qt view for cash closing report."""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.cash.application.services import CashServices
from erp.modules.cash.domain.closing_report import CashClosingReport
from erp.modules.cash.presentation.closing_report_presenter import (
    ClosingReportPresenter,
    ClosingReportView,
)
from erp.shared.application.session import CurrentSession


class ClosingReportDialog(QDialog, ClosingReportView):
    """Diálogo para exibir relatório de fechamento de caixa."""

    def __init__(
        self,
        presenter: ClosingReportPresenter | None,
        session: CurrentSession,
        session_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session_id = session_id

        self.setWindowTitle("Relatório de Fechamento de Caixa")
        self.setModal(True)
        self.resize(500, 600)

        self._setup_ui()
        if self._presenter is not None:
            self._presenter.load_report()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Scroll area for report
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._report_widget = QWidget()
        self._report_layout = QVBoxLayout(self._report_widget)
        scroll.setWidget(self._report_widget)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._close_btn = QPushButton("Fechar")
        self._close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

    def _add_row(self, label: str, value: str) -> None:
        row = QHBoxLayout()
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("font-weight: bold;")
        val = QLabel(value)
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        self._report_layout.addLayout(row)

    def _add_section(self, title: str) -> None:
        sep = QLabel(f"<b>{title}</b>")
        sep.setStyleSheet("margin-top: 10px;")
        self._report_layout.addWidget(sep)

    def set_report(self, report: CashClosingReport) -> None:
        # Clear existing
        for i in reversed(range(self._report_layout.count())):
            item = self._report_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(cast("QVBoxLayout | QHBoxLayout", child_layout))

        self._add_section("Identificação")
        self._add_row("Sessão ID", str(report.session_id))
        self._add_row("Caixa", report.register_name or "N/A")
        self._add_row("Empresa", str(report.company_id) if report.company_id else "N/A")
        self._add_row("Status", report.status)

        self._add_section("Horários")
        opened_at_str = report.opened_at.strftime("%d/%m/%Y %H:%M") if report.opened_at else "N/A"
        closed_at_str = report.closed_at.strftime("%d/%m/%Y %H:%M") if report.closed_at else "N/A"
        self._add_row("Abertura", opened_at_str)
        self._add_row("Fechamento", closed_at_str)
        self._add_row("Aberto por", report.opened_by_username)
        self._add_row("Fechado por", report.closed_by_username or "N/A")

        self._add_section("Valores em Dinheiro")
        self._add_row("Abertura", f"R$ {report.opening_amount_cents / 100:.2f}")
        self._add_row("Vendas em dinheiro", f"R$ {report.total_sales_cents / 100:.2f}")
        self._add_row("Suprimentos", f"R$ {report.total_suprimentos_cents / 100:.2f}")
        self._add_row("Sangrias", f"R$ {report.total_sangrias_cents / 100:.2f}")
        self._add_row("Esperado", f"R$ {report.expected_cash_cents / 100:.2f}")
        self._add_row("Contado", f"R$ {report.counted_cash_cents / 100:.2f}")
        self._add_row("Diferença", f"R$ {report.difference_cents / 100:.2f}")

        self._add_section("Outros Meios de Pagamento")
        self._add_row("PIX", f"R$ {report.total_pix_cents / 100:.2f}")
        self._add_row("Cartão", f"R$ {report.total_card_cents / 100:.2f}")

        self._add_section("Detalhes")
        self._add_row("Fechamento cego", "Sim" if report.blind_close else "Não")

    def _clear_layout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(cast("QVBoxLayout | QHBoxLayout", child_layout))

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def accept(self) -> None:
        super().accept()


def create_closing_report_dialog(
    services: CashServices,
    session: CurrentSession,
    session_id: int,
    engine: Engine,
    parent: QWidget | None = None,
) -> ClosingReportDialog:
    """Factory para criar o diálogo com presenter injetado."""
    dialog = ClosingReportDialog(None, session, session_id, parent)
    presenter = ClosingReportPresenter(
        view=dialog,
        services=services,
        session=session,
        session_id=session_id,
        engine=engine,
    )
    dialog._presenter = presenter
    return dialog
