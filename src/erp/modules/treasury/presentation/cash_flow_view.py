"""Cash flow view — tela detalhada de fluxo de caixa diário/mensal."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from erp.modules.treasury.application.get_cash_flow import (
    CashFlowOutput,
    DailyBreakdownItem,
    MonthlyBreakdownItem,
)
from erp.modules.treasury.presentation.cash_flow_presenter import CashFlowPresenter
from erp.shared.application.session import CurrentSession
from erp.shared.ui import SummaryCard

if TYPE_CHECKING:
    from erp.modules.treasury.application.services import TreasuryServices


class CashFlowDialog(QDialog):
    """Diálogo de fluxo de caixa com detalhamento diário e mensal."""

    def __init__(
        self,
        presenter: CashFlowPresenter | None,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session

        self.setWindowTitle("Fluxo de Caixa — Detalhado")
        self.setModal(True)
        self.resize(1000, 700)

        self._setup_ui()

        if self._presenter is not None:
            self._presenter.load_cash_flow()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Filtros
        filter_layout = QFormLayout()

        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        start_qdate = QDate.currentDate().addDays(-30)
        self._start_date.setDate(start_qdate)
        self._start_date.dateChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Data inicial:", self._start_date)

        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._end_date.dateChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Data final:", self._end_date)

        self._group_by = QComboBox()
        self._group_by.addItems(["Diário", "Mensal"])
        self._group_by.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Agrupar por:", self._group_by)

        self._refresh_btn = QPushButton("Atualizar")
        self._refresh_btn.clicked.connect(self._on_refresh)
        filter_layout.addRow("", self._refresh_btn)

        layout.addLayout(filter_layout)

        # Cards de resumo usando componentes do design system
        summary_layout = QHBoxLayout()

        self._sales_card = SummaryCard("Vendas", "R$ 0,00", "success")
        self._sales_value = self._sales_card._value_label

        self._receivables_card = SummaryCard("Recebimentos", "R$ 0,00", "info")
        self._receivables_value = self._receivables_card._value_label

        self._payables_card = SummaryCard("Pagamentos", "R$ 0,00", "danger")
        self._payables_value = self._payables_card._value_label

        self._cash_card = SummaryCard("Mov. Caixa", "R$ 0,00", "warning")
        self._cash_value = self._cash_card._value_label

        self._net_card = SummaryCard("Fluxo Líquido", "R$ 0,00", "neutral")
        self._net_value = self._net_card._value_label

        for card in [
            self._sales_card,
            self._receivables_card,
            self._payables_card,
            self._cash_card,
            self._net_card,
        ]:
            summary_layout.addWidget(card)

        layout.addLayout(summary_layout)

        # Abas: Diário / Mensal
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Aba Diário
        self._daily_widget = self._create_daily_tab()
        self._tabs.addTab(self._daily_widget, "Detalhamento Diário")

        # Aba Mensal
        self._monthly_widget = self._create_monthly_tab()
        self._tabs.addTab(self._monthly_widget, "Resumo Mensal")

        # Conectar mudança de aba para atualizar agrupamento
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # Botão fechar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _create_daily_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._daily_table = QTableWidget()
        self._daily_table.setColumnCount(6)
        self._daily_table.setHorizontalHeaderLabels(
            ["Data", "Vendas", "Recebimentos", "Pagamentos", "Mov. Caixa", "Fluxo Líquido"]
        )
        self._daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._daily_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._daily_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._daily_table)

        return widget

    def _create_monthly_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._monthly_table = QTableWidget()
        self._monthly_table.setColumnCount(6)
        self._monthly_table.setHorizontalHeaderLabels(
            ["Mês", "Vendas", "Recebimentos", "Pagamentos", "Mov. Caixa", "Fluxo Líquido"]
        )
        self._monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._monthly_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._monthly_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._monthly_table)

        return widget

    # --- CashFlowView protocol implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def set_results(self, output: CashFlowOutput) -> None:
        # Atualiza cards de resumo
        self._sales_value.setText(f"R$ {output.total_sales_cents / 100:.2f}")
        self._receivables_value.setText(f"R$ {output.total_receivables_cents / 100:.2f}")
        self._payables_value.setText(f"R$ {output.total_payables_cents / 100:.2f}")
        self._cash_value.setText(f"R$ {output.total_cash_movements_cents / 100:.2f}")

        net_variant = "success" if output.net_flow_cents >= 0 else "danger"
        self._net_value.setText(f"R$ {output.net_flow_cents / 100:.2f}")
        self._net_card.set_variant(net_variant)  # type: ignore[arg-type]

        # Atualiza tabelas detalhadas
        self._populate_daily_table(output.daily_breakdown)
        self._populate_monthly_table(output.monthly_breakdown)

    def set_date_range(self, start_date: datetime, end_date: datetime) -> None:
        self._start_date.setDate(QDate(start_date.year, start_date.month, start_date.day))
        self._end_date.setDate(QDate(end_date.year, end_date.month, end_date.day))

    def get_start_date(self) -> datetime:
        qdate = self._start_date.date()
        py_date = qdate.toPython()
        from datetime import date

        assert isinstance(py_date, date)
        return datetime.combine(py_date, datetime.min.time()).replace(tzinfo=UTC)

    def get_end_date(self) -> datetime:
        qdate = self._end_date.date()
        py_date = qdate.toPython()
        from datetime import date

        assert isinstance(py_date, date)
        return datetime.combine(py_date, datetime.max.time()).replace(tzinfo=UTC)

    def _populate_daily_table(self, daily_data: list[DailyBreakdownItem]) -> None:
        """Preenche tabela diária com breakdown."""
        self._daily_table.setRowCount(len(daily_data))
        for row, day in enumerate(daily_data):
            self._daily_table.setItem(row, 0, QTableWidgetItem(day["date"].strftime("%d/%m/%Y")))
            self._daily_table.setItem(
                row, 1, QTableWidgetItem(f"R$ {day['sales_cents'] / 100:.2f}")
            )
            self._daily_table.setItem(
                row, 2, QTableWidgetItem(f"R$ {day['receivables_cents'] / 100:.2f}")
            )
            self._daily_table.setItem(
                row, 3, QTableWidgetItem(f"R$ {day['payables_cents'] / 100:.2f}")
            )
            self._daily_table.setItem(
                row, 4, QTableWidgetItem(f"R$ {day['cash_movements_cents'] / 100:.2f}")
            )

            net = day["net_cents"]
            net_item = QTableWidgetItem(f"R$ {net / 100:.2f}")
            if net < 0:
                net_item.setForeground(Qt.GlobalColor.red)
            self._daily_table.setItem(row, 5, net_item)

    def _populate_monthly_table(self, monthly_data: list[MonthlyBreakdownItem]) -> None:
        """Preenche tabela mensal com breakdown."""
        self._monthly_table.setRowCount(len(monthly_data))
        for row, month in enumerate(monthly_data):
            self._monthly_table.setItem(row, 0, QTableWidgetItem(month["month"].strftime("%m/%Y")))
            self._monthly_table.setItem(
                row, 1, QTableWidgetItem(f"R$ {month['sales_cents'] / 100:.2f}")
            )
            self._monthly_table.setItem(
                row, 2, QTableWidgetItem(f"R$ {month['receivables_cents'] / 100:.2f}")
            )
            self._monthly_table.setItem(
                row, 3, QTableWidgetItem(f"R$ {month['payables_cents'] / 100:.2f}")
            )
            self._monthly_table.setItem(
                row, 4, QTableWidgetItem(f"R$ {month['cash_movements_cents'] / 100:.2f}")
            )

            net = month["net_cents"]
            net_item = QTableWidgetItem(f"R$ {net / 100:.2f}")
            if net < 0:
                net_item.setForeground(Qt.GlobalColor.red)
            self._monthly_table.setItem(row, 5, net_item)

    def _on_filter_changed(self) -> None:
        if self._presenter:
            self._presenter.load_cash_flow()

    def _on_refresh(self) -> None:
        if self._presenter:
            self._presenter.load_cash_flow()

    def _on_tab_changed(self, index: int) -> None:
        # Sincroniza combo de agrupamento com aba ativa
        self._group_by.setCurrentIndex(index)


def create_cash_flow_dialog(
    services: TreasuryServices,
    session: CurrentSession,
    parent: QWidget | None = None,
) -> CashFlowDialog:
    """Factory para criar o diálogo de fluxo de caixa detalhado."""
    dialog = CashFlowDialog(None, session, parent)
    presenter = CashFlowPresenter(
        view=dialog,
        services=services,
        session=session,
    )
    dialog._presenter = presenter
    return dialog
