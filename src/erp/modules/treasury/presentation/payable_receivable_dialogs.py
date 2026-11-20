"""Payables and Receivables CRUD dialogs for Treasury."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.treasury.application.services import TreasuryServices
from erp.shared.application.session import CurrentSession

if TYPE_CHECKING:
    pass


class PayableEditDialog(QDialog):
    """Diálogo para criar/editar conta a pagar."""

    def __init__(
        self,
        services: TreasuryServices,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session

        self.setWindowTitle("Nova Conta a Pagar")
        self.setModal(True)
        self.resize(500, 550)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Descrição da conta")
        form.addRow("Descrição:", self._desc_edit)

        self._supplier_edit = QLineEdit()
        self._supplier_edit.setPlaceholderText("ID do fornecedor (opcional)")
        form.addRow("Fornecedor ID:", self._supplier_edit)

        self._category_edit = QLineEdit()
        self._category_edit.setPlaceholderText("ID da categoria (opcional)")
        form.addRow("Categoria ID:", self._category_edit)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 9999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setSuffix(" R$")
        self._amount_spin.setGroupSeparatorShown(True)
        self._amount_spin.setSingleStep(0.01)
        form.addRow("Valor total (R$):", self._amount_spin)

        self._issue_date = QDateEdit()
        self._issue_date.setCalendarPopup(True)
        self._issue_date.setDate(QDate.currentDate())
        form.addRow("Data de emissão:", self._issue_date)

        self._recurrence_combo = QComboBox()
        self._recurrence_combo.addItems(
            ["Única (sem recorrência)", "Mensal", "Quinzenal", "Semanal"]
        )
        self._recurrence_combo.currentIndexChanged.connect(self._on_recurrence_changed)
        form.addRow("Recorrência:", self._recurrence_combo)

        self._recurrence_count_spin = QSpinBox()
        self._recurrence_count_spin.setRange(1, 60)
        self._recurrence_count_spin.setValue(1)
        self._recurrence_count_spin.setEnabled(False)
        form.addRow("Nº de parcelas:", self._recurrence_count_spin)

        self._first_due_date = QDateEdit()
        self._first_due_date.setCalendarPopup(True)
        self._first_due_date.setDate(QDate.currentDate().addDays(30))
        self._first_due_date.setEnabled(False)
        form.addRow("Vencimento da 1ª parcela:", self._first_due_date)

        self._interval_days_spin = QSpinBox()
        self._interval_days_spin.setRange(1, 365)
        self._interval_days_spin.setValue(30)
        self._interval_days_spin.setEnabled(False)
        form.addRow("Intervalo (dias):", self._interval_days_spin)

        self._source_type_edit = QLineEdit()
        self._source_type_edit.setPlaceholderText("Tipo de origem (ex: purchase, expense)")
        form.addRow("Tipo origem:", self._source_type_edit)

        self._source_id_edit = QLineEdit()
        self._source_id_edit.setPlaceholderText("ID da origem (opcional)")
        form.addRow("ID origem:", self._source_id_edit)

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

    def _on_recurrence_changed(self, index: int) -> None:
        has_recurrence = index > 0
        self._recurrence_count_spin.setEnabled(has_recurrence)
        self._first_due_date.setEnabled(has_recurrence)
        self._interval_days_spin.setEnabled(has_recurrence)
        if has_recurrence:
            self._recurrence_count_spin.setValue(12)
            self._first_due_date.setDate(QDate.currentDate().addDays(30))

    def _on_save_clicked(self) -> None:
        desc = self._desc_edit.text().strip()
        if not desc:
            QMessageBox.warning(self, "Erro", "Informe a descrição.")
            return

        amount = self._amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Erro", "Informe um valor maior que zero.")
            return

        try:
            from erp.modules.treasury.application.payable import CreatePayableInput

            input_data = CreatePayableInput(
                supplier_id=int(self._supplier_edit.text())
                if self._supplier_edit.text().strip()
                else None,
                category_id=int(self._category_edit.text())
                if self._category_edit.text().strip()
                else None,
                description=desc,
                total_amount_cents=round(amount * 100),
                issue_date=datetime(
                    self._issue_date.date().year(),
                    self._issue_date.date().month(),
                    self._issue_date.date().day(),
                    tzinfo=UTC,
                ),
                recurrence_type={
                    0: "none",
                    1: "monthly",
                    2: "biweekly",
                    3: "weekly",
                }[self._recurrence_combo.currentIndex()],
                recurrence_count=self._recurrence_count_spin.value()
                if self._recurrence_combo.currentIndex() > 0
                else 1,
                first_due_date=datetime(
                    self._first_due_date.date().year(),
                    self._first_due_date.date().month(),
                    self._first_due_date.date().day(),
                    tzinfo=UTC,
                )
                if self._recurrence_combo.currentIndex() > 0
                else None,
                interval_days=self._interval_days_spin.value()
                if self._recurrence_combo.currentIndex() > 0
                else 30,
                source_type=self._source_type_edit.text().strip(),
                source_id=int(self._source_id_edit.text())
                if self._source_id_edit.text().strip()
                else None,
                company_id=self._session.company_id,
            )
            output = self._services.create_payable(input_data)
            QMessageBox.information(
                self, "Sucesso", f"Conta a pagar criada (ID: {output.payable_id})"
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao criar conta a pagar: {exc}")


class ReceivableEditDialog(QDialog):
    """Diálogo para criar/editar conta a receber."""

    def __init__(
        self,
        services: TreasuryServices,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session

        self.setWindowTitle("Nova Conta a Receber")
        self.setModal(True)
        self.resize(500, 500)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Descrição da conta")
        form.addRow("Descrição:", self._desc_edit)

        self._customer_edit = QLineEdit()
        self._customer_edit.setPlaceholderText("ID do cliente (opcional)")
        form.addRow("Cliente ID:", self._customer_edit)

        self._category_edit = QLineEdit()
        self._category_edit.setPlaceholderText("ID da categoria (opcional)")
        form.addRow("Categoria ID:", self._category_edit)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 9999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setSuffix(" R$")
        self._amount_spin.setGroupSeparatorShown(True)
        self._amount_spin.setSingleStep(0.01)
        form.addRow("Valor total (R$):", self._amount_spin)

        self._issue_date = QDateEdit()
        self._issue_date.setCalendarPopup(True)
        self._issue_date.setDate(QDate.currentDate())
        form.addRow("Data de emissão:", self._issue_date)

        self._due_date = QDateEdit()
        self._due_date.setCalendarPopup(True)
        self._due_date.setDate(QDate.currentDate().addDays(30))
        form.addRow("Data de vencimento:", self._due_date)

        self._source_type_edit = QLineEdit()
        self._source_type_edit.setPlaceholderText("Tipo de origem (ex: sale, service)")
        form.addRow("Tipo origem:", self._source_type_edit)

        self._source_id_edit = QLineEdit()
        self._source_id_edit.setPlaceholderText("ID da origem (opcional)")
        form.addRow("ID origem:", self._source_id_edit)

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
        desc = self._desc_edit.text().strip()
        if not desc:
            QMessageBox.warning(self, "Erro", "Informe a descrição.")
            return

        amount = self._amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Erro", "Informe um valor maior que zero.")
            return

        try:
            from erp.modules.treasury.application.receivable import CreateReceivableInput

            input_data = CreateReceivableInput(
                customer_id=int(self._customer_edit.text())
                if self._customer_edit.text().strip()
                else None,
                category_id=int(self._category_edit.text())
                if self._category_edit.text().strip()
                else None,
                description=desc,
                total_amount_cents=round(amount * 100),
                issue_date=datetime(
                    self._issue_date.date().year(),
                    self._issue_date.date().month(),
                    self._issue_date.date().day(),
                    tzinfo=UTC,
                ),
                due_date=datetime(
                    self._due_date.date().year(),
                    self._due_date.date().month(),
                    self._due_date.date().day(),
                    tzinfo=UTC,
                ),
                source_type=self._source_type_edit.text().strip(),
                source_id=int(self._source_id_edit.text())
                if self._source_id_edit.text().strip()
                else None,
                company_id=self._session.company_id,
            )
            output = self._services.create_receivable(input_data)
            QMessageBox.information(
                self, "Sucesso", f"Conta a receber criada (ID: {output.receivable_id})"
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao criar conta a receber: {exc}")


class PayableInstallmentDialog(QDialog):
    """Diálogo para pagar uma parcela de conta a pagar."""

    def __init__(
        self,
        services: TreasuryServices,
        session: CurrentSession,
        payable_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session
        self._payable_id = payable_id

        self.setWindowTitle("Pagar Parcela")
        self.setModal(True)
        self.resize(400, 300)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._installment_spin = QSpinBox()
        self._installment_spin.setRange(1, 999)
        self._installment_spin.setValue(1)
        form.addRow("Número da parcela:", self._installment_spin)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 9999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setSuffix(" R$")
        self._amount_spin.setGroupSeparatorShown(True)
        self._amount_spin.setSingleStep(0.01)
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
        try:
            from erp.modules.treasury.application.payable import PayPayableInput

            input_data = PayPayableInput(
                payable_id=self._payable_id,
                installment_number=self._installment_spin.value(),
                amount_cents=round(self._amount_spin.value() * 100),
                paid_at=datetime(
                    self._paid_date.date().year(),
                    self._paid_date.date().month(),
                    self._paid_date.date().day(),
                    tzinfo=UTC,
                ),
            )
            self._services.pay_payable(input_data)
            QMessageBox.information(self, "Sucesso", "Parcela paga com sucesso!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao pagar parcela: {exc}")


class ReceivableReceiveDialog(QDialog):
    """Diálogo para receber uma conta a receber."""

    def __init__(
        self,
        services: TreasuryServices,
        session: CurrentSession,
        receivable_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session
        self._receivable_id = receivable_id

        self.setWindowTitle("Receber Conta")
        self.setModal(True)
        self.resize(400, 300)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 9999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setSuffix(" R$")
        self._amount_spin.setGroupSeparatorShown(True)
        self._amount_spin.setSingleStep(0.01)
        form.addRow("Valor do recebimento (R$):", self._amount_spin)

        self._received_date = QDateEdit()
        self._received_date.setCalendarPopup(True)
        self._received_date.setDate(QDate.currentDate())
        form.addRow("Data do recebimento:", self._received_date)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Confirmar Recebimento")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save_clicked(self) -> None:
        try:
            from erp.modules.treasury.application.receivable import ReceiveReceivableInput

            input_data = ReceiveReceivableInput(
                receivable_id=self._receivable_id,
                amount_cents=round(self._amount_spin.value() * 100),
                received_at=datetime(
                    self._received_date.date().year(),
                    self._received_date.date().month(),
                    self._received_date.date().day(),
                    tzinfo=UTC,
                ),
            )
            self._services.receive_receivable(input_data)
            QMessageBox.information(self, "Sucesso", "Recebimento confirmado!")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao receber conta: {exc}")


class PayableReceivableManagementWidget(QWidget):
    """Widget para gerenciar contas a pagar e receber com botões de ação."""

    def __init__(
        self,
        services: TreasuryServices,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar com botões de ação
        toolbar = QHBoxLayout()

        self._btn_new_payable = QPushButton("Nova Conta a Pagar")
        self._btn_new_payable.clicked.connect(self._on_new_payable)
        toolbar.addWidget(self._btn_new_payable)

        self._btn_new_receivable = QPushButton("Nova Conta a Receber")
        self._btn_new_receivable.clicked.connect(self._on_new_receivable)
        toolbar.addWidget(self._btn_new_receivable)

        toolbar.addStretch()

        self._btn_refresh = QPushButton("Atualizar")
        self._btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self._btn_refresh)

        layout.addLayout(toolbar)

        # Tabs para Pagar e Receber
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Aba Pagar
        self._payables_widget = self._create_payables_tab()
        self._tabs.addTab(self._payables_widget, "Contas a Pagar")

        # Aba Receber
        self._receivables_widget = self._create_receivables_tab()
        self._tabs.addTab(self._receivables_widget, "Contas a Receber")

    def _create_payables_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar de ações
        actions = QHBoxLayout()
        actions.addStretch()

        self._btn_pay_installment = QPushButton("Pagar Parcela")
        self._btn_pay_installment.clicked.connect(self._on_pay_installment)
        actions.addWidget(self._btn_pay_installment)

        self._btn_cancel_payable = QPushButton("Cancelar Conta")
        self._btn_cancel_payable.clicked.connect(self._on_cancel_payable)
        actions.addWidget(self._btn_cancel_payable)

        layout.addLayout(actions)

        # Tabela
        self._payables_table = QTableWidget()
        self._payables_table.setColumnCount(8)
        self._payables_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Descrição",
                "Fornecedor",
                "Total",
                "Status",
                "Emissão",
                "Recorrência",
                "Parcelas Pend.",
            ]
        )
        self._payables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._payables_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._payables_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._payables_table)

        return widget

    def _create_receivables_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        actions = QHBoxLayout()
        actions.addStretch()

        self._btn_receive_receivable = QPushButton("Receber")
        self._btn_receive_receivable.clicked.connect(self._on_receive_receivable)
        actions.addWidget(self._btn_receive_receivable)

        self._btn_cancel_receivable = QPushButton("Cancelar Conta")
        self._btn_cancel_receivable.clicked.connect(self._on_cancel_receivable)
        actions.addWidget(self._btn_cancel_receivable)

        layout.addLayout(actions)

        self._receivables_table = QTableWidget()
        self._receivables_table.setColumnCount(7)
        self._receivables_table.setHorizontalHeaderLabels(
            ["ID", "Descrição", "Cliente", "Total", "Status", "Emissão", "Vencimento"]
        )
        self._receivables_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._receivables_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._receivables_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._receivables_table)

        return widget

    def refresh(self) -> None:
        """Atualiza as tabelas."""
        self._load_payables()
        self._load_receivables()

    def _load_payables(self) -> None:
        try:
            output = self._services.list_payables(company_id=self._session.company_id)
            self._payables_table.setRowCount(len(output.payables))
            for row, p in enumerate(output.payables):
                self._payables_table.setItem(row, 0, QTableWidgetItem(str(p.payable_id)))
                self._payables_table.setItem(row, 1, QTableWidgetItem(p.description))
                self._payables_table.setItem(
                    row, 2, QTableWidgetItem(str(p.supplier_id) if p.supplier_id else "N/A")
                )
                self._payables_table.setItem(
                    row, 3, QTableWidgetItem(f"R$ {p.total_amount_cents / 100:.2f}")
                )
                self._payables_table.setItem(row, 4, QTableWidgetItem(p.status))
                self._payables_table.setItem(
                    row,
                    5,
                    QTableWidgetItem(p.issue_date.strftime("%d/%m/%Y") if p.issue_date else "N/A"),
                )
                self._payables_table.setItem(row, 6, QTableWidgetItem(p.recurrence_type))
                self._payables_table.setItem(
                    row,
                    7,
                    QTableWidgetItem(
                        str(
                            len(
                                [i for i in getattr(p, "installments", []) if i.status == "pending"]
                            )
                        )
                    ),
                )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar contas a pagar: {exc}")

    def _load_receivables(self) -> None:
        try:
            output = self._services.list_receivables(company_id=self._session.company_id)
            self._receivables_table.setRowCount(len(output.receivables))
            for row, r in enumerate(output.receivables):
                self._receivables_table.setItem(row, 0, QTableWidgetItem(str(r.receivable_id)))
                self._receivables_table.setItem(row, 1, QTableWidgetItem(r.description))
                self._receivables_table.setItem(
                    row, 2, QTableWidgetItem(str(r.customer_id) if r.customer_id else "N/A")
                )
                self._receivables_table.setItem(
                    row, 3, QTableWidgetItem(f"R$ {r.total_amount_cents / 100:.2f}")
                )
                self._receivables_table.setItem(row, 4, QTableWidgetItem(r.status))
                self._receivables_table.setItem(
                    row,
                    5,
                    QTableWidgetItem(r.issue_date.strftime("%d/%m/%Y") if r.issue_date else "N/A"),
                )
                self._receivables_table.setItem(
                    row,
                    6,
                    QTableWidgetItem(r.due_date.strftime("%d/%m/%Y") if r.due_date else "N/A"),
                )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar contas a receber: {exc}")

    def _on_new_payable(self) -> None:
        dialog = PayableEditDialog(self._services, self._session, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_new_receivable(self) -> None:
        dialog = ReceivableEditDialog(self._services, self._session, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_pay_installment(self) -> None:
        row = self._payables_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta a pagar.")
            return
        item = self._payables_table.item(row, 0)
        if item is None:
            QMessageBox.warning(self, "Erro", "Não foi possível ler o ID da conta a pagar.")
            return
        payable_id = int(item.text())
        dialog = PayableInstallmentDialog(self._services, self._session, payable_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_cancel_payable(self) -> None:
        row = self._payables_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta a pagar.")
            return
        item = self._payables_table.item(row, 0)
        if item is None:
            QMessageBox.warning(self, "Erro", "Não foi possível ler o ID da conta a pagar.")
            return
        payable_id = int(item.text())
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Cancelar esta conta a pagar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from erp.modules.treasury.application.cancel_payable import CancelPayableInput

                self._services.cancel_payable(CancelPayableInput(payable_id=payable_id))
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar: {exc}")

    def _on_receive_receivable(self) -> None:
        row = self._receivables_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta a receber.")
            return
        item = self._receivables_table.item(row, 0)
        if item is None:
            QMessageBox.warning(self, "Erro", "Não foi possível ler o ID da conta a receber.")
            return
        receivable_id = int(item.text())
        dialog = ReceivableReceiveDialog(self._services, self._session, receivable_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_cancel_receivable(self) -> None:
        row = self._receivables_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta a receber.")
            return
        item = self._receivables_table.item(row, 0)
        if item is None:
            QMessageBox.warning(self, "Erro", "Não foi possível ler o ID da conta a receber.")
            return
        receivable_id = int(item.text())
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Cancelar esta conta a receber?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from erp.modules.treasury.application.cancel_receivable import CancelReceivableInput

                self._services.cancel_receivable(CancelReceivableInput(receivable_id=receivable_id))
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar: {exc}")


def create_payable_receivable_dialog(
    services: TreasuryServices,
    session: CurrentSession,
    engine: Engine,
    parent: QWidget | None = None,
) -> QDialog:
    """Factory para criar o diálogo de gestão de contas a pagar/receber."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Gestão de Contas a Pagar / Receber")
    dialog.resize(900, 600)

    layout = QVBoxLayout(dialog)

    widget = PayableReceivableManagementWidget(services, session, dialog)
    layout.addWidget(widget)

    btn_close = QPushButton("Fechar")
    btn_close.clicked.connect(dialog.accept)
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(btn_close)
    layout.addLayout(btn_layout)

    return dialog
