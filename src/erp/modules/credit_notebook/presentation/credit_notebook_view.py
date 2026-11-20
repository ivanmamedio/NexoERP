"""Qt views for Credit Notebook (Caderno de Fiado)."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import (
    QAbstractTableModel,
    QDate,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.credit_notebook.application.list_customers import CreditCustomerView
from erp.modules.credit_notebook.application.list_entries import CreditEntryView
from erp.modules.credit_notebook.application.services import CreditNotebookServices
from erp.modules.credit_notebook.presentation.credit_notebook_presenter import (
    CreditNotebookPresenter,
)
from erp.shared.application.session import CurrentSession

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class CreditCustomerTableModel(QAbstractTableModel):
    """Modelo para a tabela de clientes."""

    def __init__(self, customers: list[CreditCustomerView]) -> None:
        super().__init__()
        self._customers = customers

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        _ = parent
        return len(self._customers)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        _ = parent
        return 8

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        customer = self._customers[index.row()]
        column = index.column()
        if column == 0:
            return customer.name
        if column == 1:
            return customer.phone
        if column == 2:
            return customer.email or "—"
        if column == 3:
            return (
                f"R$ {customer.credit_limit_cents / 100:.2f}"
                if customer.credit_limit_cents > 0
                else "Ilimitado"
            )
        if column == 4:
            return f"R$ {customer.current_balance_cents / 100:.2f}"
        if column == 5:
            return (
                f"R$ {customer.available_credit_cents / 100:.2f}"
                if customer.credit_limit_cents > 0
                else "Ilimitado"
            )
        if column == 6:
            return "Bloqueado" if customer.status == "blocked" else customer.status
        if column == 7:
            return str(customer.total_entries)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object | None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (
                "Nome",
                "Telefone",
                "E-mail",
                "Limite",
                "Saldo Devedor",
                "Disponível",
                "Status",
                "Lançamentos",
            )[section]
        return None

    def get_customer_at(self, row: int) -> CreditCustomerView | None:
        if 0 <= row < len(self._customers):
            return self._customers[row]
        return None


class CreditEntryTableModel(QAbstractTableModel):
    """Modelo para a tabela de lançamentos."""

    def __init__(self, entries: list[CreditEntryView]) -> None:
        super().__init__()
        self._entries = entries

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        _ = parent
        return len(self._entries)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        _ = parent
        return 9

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        entry = self._entries[index.row()]
        column = index.column()
        if column == 0:
            return entry.entry_type
        if column == 1:
            return entry.description
        if column == 2:
            if entry.entry_type == "charge":
                return f"+ R$ {entry.amount_cents / 100:.2f}"
            elif entry.entry_type == "payment":
                return f"- R$ {entry.amount_cents / 100:.2f}"
            return f"R$ {entry.amount_cents / 100:.2f}"
        if column == 3:
            return f"R$ {entry.pending_amount_cents / 100:.2f}"
        if column == 4:
            return entry.status
        if column == 5:
            return entry.due_date or "—"
        if column == 6:
            return entry.created_at[:16] if entry.created_at else "—"
        if column == 7:
            return entry.created_by_username or "—"
        if column == 8:
            return "—"  # Customer name - will be filled by presenter
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object | None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (
                "Tipo",
                "Descrição",
                "Valor",
                "Pendente",
                "Status",
                "Vencimento",
                "Data",
                "Operador",
                "Cliente",
            )[section]
        return None

    def get_entry_at(self, row: int) -> CreditEntryView | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None


class CustomerEditDialog(QDialog):
    """Diálogo para criar/editar cliente."""

    def __init__(
        self,
        presenter: CreditNotebookPresenter,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session
        self._customer: CreditCustomerView | None = None

        self.setWindowTitle("Novo Cliente")
        self.setModal(True)
        self.resize(500, 450)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Nome completo")
        form.addRow("Nome:", self._name_edit)

        self._phone_edit = QLineEdit()
        self._phone_edit.setPlaceholderText("(XX) XXXXX-XXXX")
        form.addRow("Telefone:", self._phone_edit)

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("e-mail (opcional)")
        form.addRow("E-mail:", self._email_edit)

        self._address_edit = QLineEdit()
        self._address_edit.setPlaceholderText("Endereço (opcional)")
        form.addRow("Endereço:", self._address_edit)

        self._limit_spin = QDoubleSpinBox()
        self._limit_spin.setRange(0.0, 9999999.99)
        self._limit_spin.setDecimals(2)
        self._limit_spin.setSuffix(" R$")
        self._limit_spin.setGroupSeparatorShown(True)
        self._limit_spin.setSingleStep(10.0)
        self._limit_spin.setSpecialValueText("Sem limite (0)")
        form.addRow("Limite de crédito (R$):", self._limit_spin)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["Ativo", "Bloqueado", "Inativo"])
        form.addRow("Status:", self._status_combo)

        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("Observações (opcional)")
        form.addRow("Observações:", self._notes_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Salvar")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save_clicked(self) -> None:
        if self._presenter is not None:
            self._presenter.save_customer(
                name=self._name_edit.text().strip(),
                phone=self._phone_edit.text().strip(),
                email=self._email_edit.text().strip(),
                address=self._address_edit.text().strip(),
                credit_limit_cents=round(self._limit_spin.value() * 100),
                status=["active", "blocked", "inactive"][self._status_combo.currentIndex()],
                notes=self._notes_edit.text().strip(),
            )

    def load_customer(self, customer: CreditCustomerView | None) -> None:
        self._customer = customer
        if customer is not None:
            self.setWindowTitle(f"Editar Cliente: {customer.name}")
            self._name_edit.setText(customer.name)
            self._phone_edit.setText(customer.phone)
            self._email_edit.setText(customer.email)
            self._address_edit.setText(customer.address)
            self._limit_spin.setValue(customer.credit_limit_cents / 100)
            status_map = {"active": 0, "blocked": 1, "inactive": 2}
            self._status_combo.setCurrentIndex(status_map.get(customer.status, 0))
            self._notes_edit.setText(customer.address)
        else:
            self.setWindowTitle("Novo Cliente")


class EntryEditDialog(QDialog):
    """Diálogo para criar lançamento."""

    def __init__(
        self,
        presenter: CreditNotebookPresenter,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session

        self.setWindowTitle("Novo Lançamento")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._type_combo = QComboBox()
        self._type_combo.addItems(
            [
                "Venda a prazo (Charge)",
                "Pagamento/Abatimento (Payment)",
                "Ajuste (Adjustment)",
                "Juros/Mora (Interest)",
            ]
        )
        form.addRow("Tipo:", self._type_combo)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Descrição do lançamento")
        form.addRow("Descrição:", self._desc_edit)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 9999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setSuffix(" R$")
        self._amount_spin.setGroupSeparatorShown(True)
        self._amount_spin.setSingleStep(0.01)
        form.addRow("Valor (R$):", self._amount_spin)

        self._due_date = QDateEdit()
        self._due_date.setCalendarPopup(True)
        self._due_date.setDate(QDate.currentDate().addDays(30))
        self._due_date.setSpecialValueText("Sem vencimento")
        form.addRow("Vencimento:", self._due_date)

        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("Observações (opcional)")
        form.addRow("Observações:", self._notes_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Salvar")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save_clicked(self) -> None:
        if self._presenter is not None:
            entry_type_map = {
                0: "charge",
                1: "payment",
                2: "adjustment",
                3: "interest",
            }
            self._presenter.save_entry(
                customer_id=self._customer_id,
                entry_type=entry_type_map[self._type_combo.currentIndex()],
                description=self._desc_edit.text().strip(),
                amount_cents=round(self._amount_spin.value() * 100),
                due_date=datetime.combine(
                    cast(date, self._due_date.date().toPython()), datetime.min.time()
                )
                if self._due_date.date().year() > 2000
                else None,
                notes=self._notes_edit.text().strip(),
            )

    def set_customer(self, customer_id: int) -> None:
        self._customer_id = customer_id


class PaymentDialog(QDialog):
    """Diálogo para aplicar pagamento a um lançamento."""

    def __init__(
        self,
        presenter: CreditNotebookPresenter,
        session: CurrentSession,
        entry_id: int,
        pending_amount: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session
        self._entry_id = entry_id
        self._pending_amount = pending_amount

        self.setWindowTitle("Aplicar Pagamento")
        self.setModal(True)
        self.resize(400, 250)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info
        info = QLabel(f"Valor pendente: R$ {self._pending_amount / 100:.2f}")
        info.setStyleSheet("font-weight: bold; font-size: 14px; color: #27ae60;")
        layout.addWidget(info)

        form = QFormLayout()

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, self._pending_amount / 100)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setSuffix(" R$")
        self._amount_spin.setGroupSeparatorShown(True)
        self._amount_spin.setSingleStep(0.01)
        self._amount_spin.setValue(self._pending_amount / 100)
        form.addRow("Valor do pagamento (R$):", self._amount_spin)

        self._paid_date = QDateEdit()
        self._paid_date.setCalendarPopup(True)
        self._paid_date.setDate(QDate.currentDate())
        form.addRow("Data do pagamento:", self._paid_date)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Confirmar Pagamento")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save_clicked(self) -> None:
        if self._presenter is not None:
            self._presenter.apply_payment(
                entry_id=self._entry_id,
                amount_cents=round(self._amount_spin.value() * 100),
            )


class CreditNotebookWidget(QWidget):
    """Widget principal do Caderno de Fiado."""

    def __init__(
        self,
        services: CreditNotebookServices,
        session: CurrentSession,
        engine: Engine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session
        self._engine = engine

        self._setup_ui()

        # Presenter
        self._presenter = CreditNotebookPresenter(
            view=self,
            services=services,
            session=session,
        )

        self._load_customers()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Buscar cliente por nome, telefone...")
        self._search_edit.setMinimumWidth(250)
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_edit)

        toolbar.addStretch()

        self._btn_new_customer = QPushButton("Novo Cliente")
        self._btn_new_customer.clicked.connect(self._on_new_customer)
        toolbar.addWidget(self._btn_new_customer)

        self._btn_new_entry = QPushButton("Novo Lançamento")
        self._btn_new_entry.clicked.connect(self._on_new_entry)
        self._btn_new_entry.setEnabled(False)
        toolbar.addWidget(self._btn_new_entry)

        self._btn_apply_payment = QPushButton("Receber Pagamento")
        self._btn_apply_payment.clicked.connect(self._on_apply_payment)
        self._btn_apply_payment.setEnabled(False)
        toolbar.addWidget(self._btn_apply_payment)

        self._btn_refresh = QPushButton("Atualizar")
        self._btn_refresh.clicked.connect(self._load_customers)
        toolbar.addWidget(self._btn_refresh)

        layout.addLayout(toolbar)

        # Tabs
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Aba 1: Clientes
        self._customers_widget = self._create_customers_tab()
        self._tabs.addTab(self._customers_widget, "Clientes")

        # Aba 2: Lançamentos
        self._entries_widget = self._create_entries_tab()
        self._tabs.addTab(self._entries_widget, "Lançamentos")

        # Aba 3: Relatório/Extrato
        self._statement_widget = self._create_statement_tab()
        self._tabs.addTab(self._statement_widget, "Extrato/Relatório")

        layout.setContentsMargins(8, 8, 8, 8)

    def _create_customers_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._customers_table = QTableView(self)
        self._customers_table.setSortingEnabled(True)
        self._customers_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._customers_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._customers_table.doubleClicked.connect(self._on_edit_customer)
        self._customers_table.selectionModel().selectionChanged.connect(
            self._on_customer_selection_changed
        )
        layout.addWidget(self._customers_table)

        # Proxy for search
        self._customers_proxy = QSortFilterProxyModel(self)
        self._customers_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._customers_proxy.setFilterKeyColumn(-1)
        self._customers_table.setModel(self._customers_proxy)

        return widget

    def _create_entries_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter by customer
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por cliente:"))

        self._customer_filter_combo = QComboBox()
        self._customer_filter_combo.addItem("Todos", None)
        self._customer_filter_combo.currentIndexChanged.connect(self._on_entry_filter_changed)
        filter_layout.addWidget(self._customer_filter_combo)

        filter_layout.addStretch()

        self._type_filter_combo = QComboBox()
        self._type_filter_combo.addItems(
            ["Todos", "Vendas (Charge)", "Pagamentos (Payment)", "Ajustes", "Juros"]
        )
        self._type_filter_combo.currentIndexChanged.connect(self._on_entry_filter_changed)
        filter_layout.addWidget(self._type_filter_combo)

        self._status_filter_combo = QComboBox()
        self._status_filter_combo.addItems(
            ["Todos", "Pendentes", "Pagos", "Parciais", "Cancelados"]
        )
        self._status_filter_combo.currentIndexChanged.connect(self._on_entry_filter_changed)
        filter_layout.addWidget(self._status_filter_combo)

        layout.addLayout(filter_layout)

        self._entries_table = QTableView(self)
        self._entries_table.setSortingEnabled(True)
        self._entries_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._entries_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._entries_table.doubleClicked.connect(self._on_apply_payment_to_entry)
        self._entries_table.selectionModel().selectionChanged.connect(
            self._on_entry_selection_changed
        )
        layout.addWidget(self._entries_table)

        self._entries_proxy = QSortFilterProxyModel(self)
        self._entries_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._entries_proxy.setFilterKeyColumn(-1)
        self._entries_table.setModel(self._entries_proxy)

        return widget

    def _create_statement_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Customer selector for statement
        stmt_filter = QHBoxLayout()
        stmt_filter.addWidget(QLabel("Cliente:"))

        self._statement_customer_combo = QComboBox()
        self._statement_customer_combo.addItem("Selecione um cliente", None)
        self._statement_customer_combo.currentIndexChanged.connect(
            self._on_statement_customer_changed
        )
        stmt_filter.addWidget(self._statement_customer_combo)

        stmt_filter.addStretch()

        self._btn_export_pdf = QPushButton("Exportar PDF")
        self._btn_export_pdf.clicked.connect(self._on_export_pdf)
        stmt_filter.addWidget(self._btn_export_pdf)

        self._btn_export_xlsx = QPushButton("Exportar Planilha")
        self._btn_export_xlsx.clicked.connect(self._on_export_xlsx)
        stmt_filter.addWidget(self._btn_export_xlsx)

        layout.addLayout(stmt_filter)

        # Statement table
        self._statement_table = QTableView(self)
        self._statement_table.setSortingEnabled(True)
        self._statement_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._statement_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._statement_table)

        # Summary
        summary_layout = QHBoxLayout()
        self._stmt_total_charges = QLabel("Total Vendas: R$ 0,00")
        self._stmt_total_payments = QLabel("Total Pagamentos: R$ 0,00")
        self._stmt_balance = QLabel("Saldo Devedor: R$ 0,00")
        self._stmt_balance.setStyleSheet("font-weight: bold; font-size: 14px; color: #c0392b;")

        summary_layout.addWidget(self._stmt_total_charges)
        summary_layout.addWidget(self._stmt_total_payments)
        summary_layout.addStretch()
        summary_layout.addWidget(self._stmt_balance)

        layout.addLayout(summary_layout)

        return widget

    def _load_customers(self) -> None:
        try:
            output = self._services.list_customers(
                company_id=self._session.company_id, search_query=self._search_edit.text()
            )
            self._customers_source = output.customers
            self._customers_model = CreditCustomerTableModel(list(self._customers_source))
            self._customers_proxy.setSourceModel(self._customers_model)
            self._customers_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            self._customers_table.horizontalHeader().setStretchLastSection(True)

            # Update customer filter combos
            self._update_customer_combos()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar clientes: {exc}")

    def _update_customer_combos(self) -> None:
        # Entry filter combo
        current = self._customer_filter_combo.currentData()
        self._customer_filter_combo.blockSignals(True)
        self._customer_filter_combo.clear()
        self._customer_filter_combo.addItem("Todos", None)
        for c in self._customers_source:
            self._customer_filter_combo.addItem(c.name, c.customer_id)
        idx = self._customer_filter_combo.findData(current)
        if idx >= 0:
            self._customer_filter_combo.setCurrentIndex(idx)
        self._customer_filter_combo.blockSignals(False)

        # Statement combo
        current_stmt = self._statement_customer_combo.currentData()
        self._statement_customer_combo.blockSignals(True)
        self._statement_customer_combo.clear()
        self._statement_customer_combo.addItem("Selecione um cliente", None)
        for c in self._customers_source:
            self._statement_customer_combo.addItem(c.name, c.customer_id)
        idx = self._statement_customer_combo.findData(current_stmt)
        if idx >= 0:
            self._statement_customer_combo.setCurrentIndex(idx)
        self._statement_customer_combo.blockSignals(False)

    def _load_entries(self) -> None:
        try:
            customer_id = self._customer_filter_combo.currentData()
            status_map = {
                0: None,  # Todos
                1: "pending",  # Pendentes
                2: "paid",  # Pagos
                3: "partial",  # Parciais
                4: "cancelled",  # Cancelados
            }
            type_map = {
                0: None,
                1: "charge",
                2: "payment",
                3: "adjustment",
                4: "interest",
            }

            output = self._services.list_entries(
                customer_id=customer_id,
                company_id=self._session.company_id,
                status=status_map[self._status_filter_combo.currentIndex()],
                entry_type=type_map[self._type_filter_combo.currentIndex()],
            )

            # Populate customer names
            customer_names = {c.customer_id: c.name for c in self._customers_source}
            entries_with_names = []
            for entry in output.entries:
                if not entry.customer_name:
                    entry = CreditEntryView(
                        entry_id=entry.entry_id,
                        customer_id=entry.customer_id,
                        customer_name=customer_names.get(
                            entry.customer_id, f"ID {entry.customer_id}"
                        ),
                        entry_type=entry.entry_type,
                        description=entry.description,
                        amount_cents=entry.amount_cents,
                        status=entry.status,
                        due_date=entry.due_date,
                        paid_amount_cents=entry.paid_amount_cents,
                        pending_amount_cents=entry.pending_amount_cents,
                        created_at=entry.created_at,
                        created_by_username=entry.created_by_username,
                    )
                entries_with_names.append(entry)

            self._entries_source = entries_with_names
            self._entries_model = CreditEntryTableModel(list(self._entries_source))
            self._entries_proxy.setSourceModel(self._entries_model)
            self._entries_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            self._entries_table.horizontalHeader().setStretchLastSection(True)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar lançamentos: {exc}")

    def _load_statement(self, customer_id: int) -> None:
        try:
            output = self._services.list_entries(
                customer_id=customer_id,
                company_id=self._session.company_id,
            )

            total_charges = sum(e.amount_cents for e in output.entries if e.entry_type == "charge")
            total_payments = sum(
                e.amount_cents for e in output.entries if e.entry_type == "payment"
            )
            balance = total_charges - total_payments

            self._stmt_total_charges.setText(f"Total Vendas: R$ {total_charges / 100:.2f}")
            self._stmt_total_payments.setText(f"Total Pagamentos: R$ {total_payments / 100:.2f}")
            self._stmt_balance.setText(f"Saldo Devedor: R$ {balance / 100:.2f}")

            # Create statement model
            self._statement_source = output.entries
            self._statement_model = CreditEntryTableModel(list(self._statement_source))
            self._statement_table.setModel(self._statement_model)
            self._statement_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            self._statement_table.horizontalHeader().setStretchLastSection(True)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar extrato: {exc}")

    def _on_search_changed(self, text: str) -> None:
        self._customers_proxy.setFilterFixedString(text)

    def _on_customer_selection_changed(self) -> None:
        has_selection = self._customers_table.selectionModel().hasSelection()
        self._btn_new_entry.setEnabled(has_selection)
        self._btn_apply_payment.setEnabled(has_selection)

    def _on_entry_selection_changed(self) -> None:
        self._entries_table.selectionModel().hasSelection()
        # Could enable actions here

    def _on_entry_filter_changed(self) -> None:
        self._load_entries()

    def _on_statement_customer_changed(self, index: int) -> None:
        customer_id = self._statement_customer_combo.currentData()
        if customer_id:
            self._load_statement(customer_id)
        else:
            self._statement_table.setModel(None)
            self._stmt_total_charges.setText("Total Vendas: R$ 0,00")
            self._stmt_total_payments.setText("Total Pagamentos: R$ 0,00")
            self._stmt_balance.setText("Saldo Devedor: R$ 0,00")

    def _on_new_customer(self) -> None:
        assert self._presenter is not None
        dialog = CustomerEditDialog(self._presenter, self._session, self)
        dialog._presenter = self._presenter
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_customers()

    def _on_edit_customer(self) -> None:
        indexes = self._customers_table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._customers_proxy.mapToSource(proxy_index)
        customer = self._customers_model.get_customer_at(source_index.row())
        if customer is None:
            return

        dialog = CustomerEditDialog(self._presenter, self._session, self)
        dialog._presenter = self._presenter
        dialog.load_customer(customer)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_customers()

    def _on_new_entry(self) -> None:
        indexes = self._customers_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente primeiro.")
            return
        proxy_index = indexes[0]
        source_index = self._customers_proxy.mapToSource(proxy_index)
        customer = self._customers_model.get_customer_at(source_index.row())
        if customer is None:
            return

        assert self._presenter is not None
        dialog = EntryEditDialog(self._presenter, self._session, self)
        dialog._presenter = self._presenter
        dialog.set_customer(customer.customer_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_entries()

    def _on_apply_payment(self) -> None:
        indexes = self._customers_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente para ver seus lançamentos pendentes."
            )
            return
        # Switch to entries tab and filter by customer
        self._tabs.setCurrentIndex(1)
        self._customer_filter_combo.setCurrentIndex(
            self._customer_filter_combo.findData(indexes[0].data())
        )

    def _on_apply_payment_to_entry(self) -> None:
        indexes = self._entries_table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._entries_proxy.mapToSource(proxy_index)
        entry = self._entries_model.get_entry_at(source_index.row())
        if entry is None or entry.pending_amount_cents <= 0:
            return

        dialog = PaymentDialog(
            self._presenter, self._session, entry.entry_id, entry.pending_amount_cents, self
        )
        dialog._presenter = self._presenter
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_entries()
            self._load_customers()

    def _on_export_pdf(self) -> None:
        QMessageBox.information(
            self, "Em desenvolvimento", "Exportação PDF será implementada em breve."
        )

    def _on_export_xlsx(self) -> None:
        QMessageBox.information(
            self, "Em desenvolvimento", "Exportação Planilha será implementada em breve."
        )

    # --- View protocol implementation ---

    def set_customers(self, customers: list[CreditCustomerView]) -> None:
        self._customers_source = tuple(customers)
        self._customers_model = CreditCustomerTableModel(list(customers))
        self._customers_proxy.setSourceModel(self._customers_model)
        self._customers_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._customers_table.horizontalHeader().setStretchLastSection(True)
        self._update_customer_combos()

    def set_entries(self, entries: list[CreditEntryView]) -> None:
        # Populate customer names
        customer_names = {c.customer_id: c.name for c in self._customers_source}
        entries_with_names = []
        for entry in entries:
            if not entry.customer_name:
                entry = CreditEntryView(
                    entry_id=entry.entry_id,
                    customer_id=entry.customer_id,
                    customer_name=customer_names.get(entry.customer_id, f"ID {entry.customer_id}"),
                    entry_type=entry.entry_type,
                    description=entry.description,
                    amount_cents=entry.amount_cents,
                    status=entry.status,
                    due_date=entry.due_date,
                    paid_amount_cents=entry.paid_amount_cents,
                    pending_amount_cents=entry.pending_amount_cents,
                    created_at=entry.created_at,
                    created_by_username=entry.created_by_username,
                )
            entries_with_names.append(entry)

        self._entries_source = entries_with_names
        self._entries_model = CreditEntryTableModel(list(self._entries_source))
        self._entries_proxy.setSourceModel(self._entries_model)
        self._entries_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._entries_table.horizontalHeader().setStretchLastSection(True)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def show_success(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)


def create_credit_notebook_dialog(
    services: CreditNotebookServices,
    session: CurrentSession,
    engine: Engine,
    parent: QWidget | None = None,
) -> QDialog:
    """Factory para criar o diálogo do Caderno de Fiado."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Caderno de Fiado — Controle de Crédito de Clientes")
    dialog.resize(1100, 750)

    layout = QVBoxLayout(dialog)

    widget = CreditNotebookWidget(services, session, engine, dialog)
    layout.addWidget(widget)

    btn_close = QPushButton("Fechar")
    btn_close.clicked.connect(dialog.accept)
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(btn_close)
    layout.addLayout(btn_layout)

    return dialog
