"""Qt view for Treasury dashboard with tabs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict

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
from sqlalchemy.engine import Engine

from erp.modules.treasury.application.services import TreasuryServices
from erp.modules.treasury.presentation.treasury_presenter import TreasuryDashboardPresenter
from erp.shared.application.session import CurrentSession


class TreasuryDashboardDialog(QDialog):
    """Diálogo principal de tesouraria com abas."""

    def __init__(
        self,
        presenter: TreasuryDashboardPresenter | None,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session

        self.setWindowTitle("Tesouraria — Fluxo de Caixa, Contas a Pagar/Receber")
        self.setModal(True)
        self.resize(900, 650)

        self._setup_ui()

        # Carregar dados iniciais
        if self._presenter is not None:
            self._presenter.load_all()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Filtros globais no topo
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

        self._days_ahead = QComboBox()
        self._days_ahead.addItems(["7 dias", "15 dias", "30 dias", "60 dias", "90 dias"])
        self._days_ahead.setCurrentIndex(0)
        self._days_ahead.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addRow("Alertas (próx.):", self._days_ahead)

        self._refresh_btn = QPushButton("Atualizar")
        self._refresh_btn.clicked.connect(self._on_refresh)
        filter_layout.addRow("", self._refresh_btn)

        layout.addLayout(filter_layout)

        # Abas
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Aba 1: Fluxo de Caixa
        self._cash_flow_widget = self._create_cash_flow_tab()
        self._tabs.addTab(self._cash_flow_widget, "Fluxo de Caixa")

        # Aba 2: Contas a Pagar
        self._payables_widget = self._create_payables_tab()
        self._tabs.addTab(self._payables_widget, "Contas a Pagar")

        # Aba 3: Contas a Receber
        self._receivables_widget = self._create_receivables_tab()
        self._tabs.addTab(self._receivables_widget, "Contas a Receber")

        # Aba 4: Alertas
        self._alerts_widget = self._create_alerts_tab()
        self._tabs.addTab(self._alerts_widget, "⚠ Alertas")

        # Aba 5: Resumo por Categoria
        self._category_widget = self._create_category_tab()
        self._tabs.addTab(self._category_widget, "Resumo por Categoria")

        # Botão fechar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _create_cash_flow_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cards de resumo
        summary_layout = QHBoxLayout()

        self._cf_sales_card, self._cf_sales_value = self._create_summary_card("Vendas", "R$ 0,00", "#27ae60")
        self._cf_receivables_card, self._cf_receivables_value = self._create_summary_card("Recebimentos", "R$ 0,00", "#2980b9")
        self._cf_payables_card, self._cf_payables_value = self._create_summary_card("Pagamentos", "R$ 0,00", "#c0392b")
        self._cf_cash_card, self._cf_cash_value = self._create_summary_card("Mov. Caixa", "R$ 0,00", "#8e44ad")
        self._cf_net_card, self._cf_net_value = self._create_summary_card("Fluxo Líquido", "R$ 0,00", "#2c3e50")

        for card in [
            self._cf_sales_card,
            self._cf_receivables_card,
            self._cf_payables_card,
            self._cf_cash_card,
            self._cf_net_card,
        ]:
            summary_layout.addWidget(card)

        layout.addLayout(summary_layout)

        # Detalhes (placeholder para futuras expansões)
        details_label = QLabel("Detalhamento por data disponível em relatórios específicos.")
        details_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-top: 10px;")
        details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(details_label)
        layout.addStretch()

        return widget

    def _create_summary_card(self, title: str, value: str, color: str) -> tuple[QWidget, QLabel]:
        card = QWidget()
        card.setFixedHeight(100)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 8px;
                color: white;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        value_label.setObjectName("valueLabel")
        layout.addWidget(value_label)

        return card, value_label

    def _create_payables_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tabela
        self._payables_table = QTableWidget()
        self._payables_table.setColumnCount(7)
        self._payables_table.setHorizontalHeaderLabels([
            "ID", "Descrição", "Fornecedor", "Total", "Status", "Vencimento Próx.", "Parcelas Pend."
        ])
        self._payables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._payables_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._payables_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._payables_table)

        return widget

    def _create_receivables_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._receivables_table = QTableWidget()
        self._receivables_table.setColumnCount(7)
        self._receivables_table.setHorizontalHeaderLabels([
            "ID", "Descrição", "Cliente", "Total", "Status", "Vencimento", "Pendente"
        ])
        self._receivables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._receivables_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._receivables_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._receivables_table)

        return widget

    def _create_alerts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Contadores
        counters_layout = QHBoxLayout()
        self._alert_overdue_pay, self._alert_overdue_pay_value = self._create_alert_counter("Pagar Vencidas", "0", "#c0392b")
        self._alert_due_soon_pay, self._alert_due_soon_pay_value = self._create_alert_counter("Pagar Próx. 7d", "0", "#e67e22")
        self._alert_overdue_recv, self._alert_overdue_recv_value = self._create_alert_counter("Receber Vencidas", "0", "#c0392b")
        self._alert_due_soon_recv, self._alert_due_soon_recv_value = self._create_alert_counter("Receber Próx. 7d", "0", "#27ae60")

        for c in [
            self._alert_overdue_pay,
            self._alert_due_soon_pay,
            self._alert_overdue_recv,
            self._alert_due_soon_recv,
        ]:
            counters_layout.addWidget(c)

        layout.addLayout(counters_layout)

        # Tabela de alertas de pagar
        pay_label = QLabel("<b>Contas a Pagar — Vencidas / Próximas</b>")
        layout.addWidget(pay_label)

        self._alerts_pay_table = QTableWidget()
        self._alerts_pay_table.setColumnCount(5)
        self._alerts_pay_table.setHorizontalHeaderLabels([
            "Descrição", "Vencimento", "Valor Parcela", "Status", "Dias"
        ])
        self._alerts_pay_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._alerts_pay_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._alerts_pay_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._alerts_pay_table)

        # Tabela de alertas de receber
        recv_label = QLabel("<b>Contas a Receber — Vencidas / Próximas</b>")
        layout.addWidget(recv_label)

        self._alerts_recv_table = QTableWidget()
        self._alerts_recv_table.setColumnCount(5)
        self._alerts_recv_table.setHorizontalHeaderLabels([
            "Descrição", "Vencimento", "Valor Pendente", "Status", "Dias"
        ])
        self._alerts_recv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._alerts_recv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._alerts_recv_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._alerts_recv_table)

        return widget

    def _create_alert_counter(self, title: str, value: str, color: str) -> tuple[QWidget, QLabel]:
        card = QWidget()
        card.setFixedHeight(80)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 8px;
                color: white;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        value_label.setObjectName("valueLabel")
        layout.addWidget(value_label)

        return card, value_label

    def _create_category_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cards de totais
        totals_layout = QHBoxLayout()
        self._cat_income_card, self._cat_income_value = self._create_summary_card("Total Receitas", "R$ 0,00", "#27ae60")
        self._cat_expense_card, self._cat_expense_value = self._create_summary_card("Total Despesas", "R$ 0,00", "#c0392b")
        self._cat_net_card, self._cat_net_value = self._create_summary_card("Saldo Líquido", "R$ 0,00", "#2c3e50")

        for card in [self._cat_income_card, self._cat_expense_card, self._cat_net_card]:
            totals_layout.addWidget(card)

        layout.addLayout(totals_layout)

        # Tabela por categoria
        self._category_table = QTableWidget()
        self._category_table.setColumnCount(4)
        self._category_table.setHorizontalHeaderLabels([
            "Categoria", "Tipo", "Quantidade", "Total"
        ])
        self._category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._category_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._category_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._category_table)

        return widget

    # --- TreasuryDashboardView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def set_cash_flow(self, output: Any) -> None:
        from erp.modules.treasury.application.get_cash_flow import CashFlowOutput
        assert isinstance(output, CashFlowOutput)
        self._cf_sales_value.setText(f"R$ {output.total_sales_cents / 100:.2f}")
        self._cf_receivables_value.setText(f"R$ {output.total_receivables_cents / 100:.2f}")
        self._cf_payables_value.setText(f"R$ {output.total_payables_cents / 100:.2f}")
        self._cf_cash_value.setText(f"R$ {output.total_cash_movements_cents / 100:.2f}")

        net_color = "#27ae60" if output.net_flow_cents >= 0 else "#c0392b"
        self._cf_net_value.setText(f"R$ {output.net_flow_cents / 100:.2f}")
        self._cf_net_card.setStyleSheet(f"""
            QWidget {{
                background-color: {net_color};
                border-radius: 8px;
                color: white;
            }}
        """)

    def set_payables(self, output: Any) -> None:
        from erp.modules.treasury.application.list_payables_by_due_date import (
            ListPayablesByDueDateOutput,
        )
        assert isinstance(output, ListPayablesByDueDateOutput)
        self._payables_table.setRowCount(len(output.payables))
        for row, p in enumerate(output.payables):
            # Contar parcelas pendentes
            pending_installments = [i for i in p.installments if i.status == "pending"]
            next_due = min((i.due_date for i in pending_installments), default=None)

            self._payables_table.setItem(row, 0, QTableWidgetItem(str(p.payable_id)))
            self._payables_table.setItem(row, 1, QTableWidgetItem(p.description))
            self._payables_table.setItem(row, 2, QTableWidgetItem(str(p.supplier_id) if p.supplier_id else "N/A"))
            self._payables_table.setItem(row, 3, QTableWidgetItem(f"R$ {p.total_amount_cents / 100:.2f}"))
            self._payables_table.setItem(row, 4, QTableWidgetItem(p.status))
            self._payables_table.setItem(row, 5, QTableWidgetItem(
                next_due.strftime("%d/%m/%Y") if next_due else "N/A"
            ))
            self._payables_table.setItem(row, 6, QTableWidgetItem(str(len(pending_installments))))

    def set_receivables(self, output: Any) -> None:
        from erp.modules.treasury.application.list_receivables_by_due_date import (
            ListReceivablesByDueDateOutput,
        )
        assert isinstance(output, ListReceivablesByDueDateOutput)
        self._receivables_table.setRowCount(len(output.receivables))
        for row, r in enumerate(output.receivables):
            self._receivables_table.setItem(row, 0, QTableWidgetItem(str(r.receivable_id)))
            self._receivables_table.setItem(row, 1, QTableWidgetItem(r.description))
            self._receivables_table.setItem(row, 2, QTableWidgetItem(str(r.customer_id) if r.customer_id else "N/A"))
            self._receivables_table.setItem(row, 3, QTableWidgetItem(f"R$ {r.total_amount_cents / 100:.2f}"))
            self._receivables_table.setItem(row, 4, QTableWidgetItem(r.status))
            self._receivables_table.setItem(row, 5, QTableWidgetItem(
                r.due_date.strftime("%d/%m/%Y") if r.due_date else "N/A"
            ))
            self._receivables_table.setItem(row, 6, QTableWidgetItem(f"R$ {r.pending_amount_cents / 100:.2f}"))

    def set_alerts(self, payables_output: Any, receivables_output: Any) -> None:
        from erp.modules.treasury.application.get_payables_due_soon import GetPayablesDueSoonOutput
        from erp.modules.treasury.application.get_receivables_due_soon import (
            GetReceivablesDueSoonOutput,
        )
        assert isinstance(payables_output, GetPayablesDueSoonOutput)
        assert isinstance(receivables_output, GetReceivablesDueSoonOutput)
        # Contadores
        self._alert_overdue_pay_value.setText(str(payables_output.overdue_count))
        self._alert_due_soon_pay_value.setText(str(payables_output.due_soon_count))
        self._alert_overdue_recv_value.setText(str(receivables_output.overdue_count))
        self._alert_due_soon_recv_value.setText(str(receivables_output.due_soon_count))

        # Tabela alertas pagar
        class PayAlertRow(TypedDict):
            desc: str
            due: datetime
            amount: int
            status: str
            days: int

        pay_rows: list[PayAlertRow] = []
        for p in payables_output.payables:
            for inst in p.installments:
                if inst.status != "pending":
                    continue
                days = (inst.due_date - datetime.now(UTC)).days
                pay_rows.append(PayAlertRow(
                    desc=p.description,
                    due=inst.due_date,
                    amount=inst.amount_cents,
                    status=inst.status,
                    days=days,
                ))

        pay_rows.sort(key=lambda x: x["days"])
        self._alerts_pay_table.setRowCount(len(pay_rows))
        for row, item in enumerate(pay_rows):
            self._alerts_pay_table.setItem(row, 0, QTableWidgetItem(item["desc"]))
            self._alerts_pay_table.setItem(row, 1, QTableWidgetItem(item["due"].strftime("%d/%m/%Y")))
            self._alerts_pay_table.setItem(row, 2, QTableWidgetItem(f"R$ {item['amount'] / 100:.2f}"))
            self._alerts_pay_table.setItem(row, 3, QTableWidgetItem(item["status"]))
            days_text = f"{item['days']}d" if item["days"] >= 0 else f"VENCIDO {abs(item['days'])}d"
            self._alerts_pay_table.setItem(row, 4, QTableWidgetItem(days_text))

        # Tabela alertas receber
        class RecvAlertRow(TypedDict):
            desc: str
            due: datetime | None
            amount: int
            status: str
            days: int

        recv_rows: list[RecvAlertRow] = []
        for r in receivables_output.receivables:
            if r.pending_amount_cents <= 0:
                continue
            recv_rows.append(RecvAlertRow(
                desc=r.description,
                due=r.due_date,
                amount=r.pending_amount_cents,
                status=r.status,
                days=r.days_overdue,
            ))

        recv_rows.sort(key=lambda x: (x["days"] < 0, x["days"]))
        self._alerts_recv_table.setRowCount(len(recv_rows))
        for row, item in enumerate(recv_rows):  # type: ignore[assignment]
            self._alerts_recv_table.setItem(row, 0, QTableWidgetItem(item["desc"]))
            self._alerts_recv_table.setItem(row, 1, QTableWidgetItem(
                item["due"].strftime("%d/%m/%Y") if item["due"] else "N/A"
            ))
            self._alerts_recv_table.setItem(row, 2, QTableWidgetItem(f"R$ {item['amount'] / 100:.2f}"))
            self._alerts_recv_table.setItem(row, 3, QTableWidgetItem(item["status"]))
            days_text = f"{item['days']}d" if item["days"] >= 0 else f"VENCIDO {abs(item['days'])}d"
            self._alerts_recv_table.setItem(row, 4, QTableWidgetItem(days_text))

    def set_category_summary(self, output: Any) -> None:
        from erp.modules.treasury.application.get_category_summary import GetCategorySummaryOutput
        assert isinstance(output, GetCategorySummaryOutput)
        self._cat_income_value.setText(f"R$ {output.total_income_cents / 100:.2f}")
        self._cat_expense_value.setText(f"R$ {output.total_expense_cents / 100:.2f}")

        net_color = "#27ae60" if output.net_cents >= 0 else "#c0392b"
        self._cat_net_value.setText(f"R$ {output.net_cents / 100:.2f}")
        self._cat_net_card.setStyleSheet(f"""
            QWidget {{
                background-color: {net_color};
                border-radius: 8px;
                color: white;
            }}
        """)

        self._category_table.setRowCount(len(output.rows))
        for row, cat in enumerate(output.rows):
            kind_text = "Receita" if cat.category_kind == "income" else "Despesa"
            self._category_table.setItem(row, 0, QTableWidgetItem(cat.category_name))
            self._category_table.setItem(row, 1, QTableWidgetItem(kind_text))
            self._category_table.setItem(row, 2, QTableWidgetItem(str(cat.entry_count)))
            self._category_table.setItem(row, 3, QTableWidgetItem(f"R$ {cat.total_cents / 100:.2f}"))

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

    def get_days_ahead(self) -> int:
        idx = self._days_ahead.currentIndex()
        return [7, 15, 30, 60, 90][idx]

    def _on_filter_changed(self) -> None:
        if self._presenter:
            self._presenter.load_all()

    def _on_refresh(self) -> None:
        if self._presenter:
            self._presenter.load_all()

    def accept(self) -> None:
        super().accept()


def create_treasury_dashboard_dialog(
    services: TreasuryServices,
    session: CurrentSession,
    engine: Engine,
    parent: QWidget | None = None,
) -> TreasuryDashboardDialog:
    """Factory para criar o dashboard de tesouraria com presenter injetado."""
    dialog = TreasuryDashboardDialog(None, session, parent)
    presenter = TreasuryDashboardPresenter(
        view=dialog,
        services=services,
        session=session,
        engine=engine,
    )
    dialog._presenter = presenter
    return dialog