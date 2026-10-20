"""Tela do PDV (PySide6) — 100% operável por teclado.

Atalhos:
  Enter  adiciona o código/SKU/nome digitado (aceita "3*código")
  F2     pagamento misto
  F4     desconto (com autorização de supervisor quando necessário)
  F6     cancela o item selecionado
  F8     cancela a venda
  Esc    volta (fecha a tela)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from erp.modules.identity.application.services import IdentityServices
from erp.modules.sales.application.services import SalesServices
from erp.modules.sales.presentation.payment_dialog import PaymentDialog
from erp.modules.sales.presentation.pin_dialog import PinDialog
from erp.modules.sales.presentation.pos_presenter import (
    PaymentEntry,
    PosItemRow,
    PosPresenter,
    ProductOption,
)
from erp.shared.application.session import CurrentSession
from erp.shared.domain.value_objects import Money

_SEARCH_DEBOUNCE_MS = 300


def _format_quantity(thousandths: int) -> str:
    whole = thousandths // 1000
    fraction = thousandths % 1000
    if fraction == 0:
        return str(whole)
    return f"{whole},{fraction:03d}"


class PosDialog(QDialog):
    """Janela do PDV: leitura sempre focada, tabela de itens e total grande.

    Implementa estruturalmente o protocolo ``PosView`` (herdar de um Protocol
    junto de QDialog causa conflito de metaclasse com o PySide6).
    """

    def __init__(
        self,
        presenter: PosPresenter | None,
        session: CurrentSession,
        session_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session
        self._session_id = session_id

        self.setWindowTitle("PDV — Ponto de Venda")
        self.setModal(True)
        self.resize(900, 620)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._on_search_timeout)

        self._build_ui()

    def set_presenter(self, presenter: PosPresenter) -> None:
        self._presenter = presenter

    # --- construção da UI ---------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self._operator_label = QLabel("Operador: —")
        self._operator_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self._operator_label)
        header.addStretch()
        session_text = (
            f"Sessão de caixa: {self._session_id}"
            if self._session_id is not None
            else "Sem sessão de caixa"
        )
        self._session_label = QLabel(session_text)
        self._session_label.setStyleSheet("color: gray;")
        header.addWidget(self._session_label)
        layout.addLayout(header)

        self._scan_input = QLineEdit()
        self._scan_input.setPlaceholderText(
            "Leia o código de barras ou digite o nome (Enter) — multiplicador: 3*código"
        )
        self._scan_input.setClearButtonEnabled(True)
        self._scan_input.setStyleSheet("font-size: 18px; padding: 6px;")
        self._scan_input.returnPressed.connect(self._on_scan_return)
        self._scan_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._scan_input)

        self._suggestions = QListWidget()
        self._suggestions.setMaximumHeight(120)
        self._suggestions.setVisible(False)
        self._suggestions.itemActivated.connect(self._on_suggestion_activated)
        layout.addWidget(self._suggestions)

        self._items_table = QTableWidget(0, 5)
        self._items_table.setHorizontalHeaderLabels(["Descrição", "Qtd", "Un.", "Preço", "Total"])
        self._items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._items_table.verticalHeader().setVisible(False)
        header_view = self._items_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3, 4):
            header_view.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._items_table, stretch=1)

        totals = QHBoxLayout()
        self._subtotal_label = QLabel("Subtotal: R$ 0,00")
        self._discount_label = QLabel("Desconto: R$ 0,00")
        self._subtotal_label.setStyleSheet("font-size: 14px;")
        self._discount_label.setStyleSheet("font-size: 14px;")
        totals.addWidget(self._subtotal_label)
        totals.addWidget(self._discount_label)
        totals.addStretch()
        totals.addWidget(QLabel("TOTAL:"))
        self._total_label = QLabel("R$ 0,00")
        self._total_label.setStyleSheet("font-size: 34px; font-weight: bold; color: #0b5394;")
        totals.addWidget(self._total_label)
        layout.addLayout(totals)

        buttons = QHBoxLayout()
        for text, handler in (
            ("F2 Pagamento", self._on_payment),
            ("F4 Desconto", self._on_discount),
            ("F6 Cancelar item", self._on_cancel_item),
            ("F8 Cancelar venda", self._on_cancel_sale),
            ("Esc Sair", self._on_escape),
        ):
            button = QPushButton(text)
            button.clicked.connect(handler)
            buttons.addWidget(button)
        layout.addLayout(buttons)

    # --- eventos de teclado -------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """F-keys funcionam mesmo com o foco no campo de leitura."""
        key = event.key()
        if key == Qt.Key.Key_F2:
            self._on_payment()
        elif key == Qt.Key.Key_F4:
            self._on_discount()
        elif key == Qt.Key.Key_F6:
            self._on_cancel_item()
        elif key == Qt.Key.Key_F8:
            self._on_cancel_sale()
        elif key == Qt.Key.Key_Escape:
            self._on_escape()
        elif (
            key == Qt.Key.Key_Down
            and self._suggestions.isVisible()
            and self._suggestions.count() > 0
        ):
            # Seta para baixo: navega nas sugestões sem tirar a mão do teclado.
            self._suggestions.setCurrentRow(0)
            self._suggestions.setFocus()
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def _on_scan_return(self) -> None:
        if self._presenter is not None:
            self._presenter.on_scan_entered()

    def _on_text_changed(self, _text: str) -> None:
        self._search_timer.start()

    def _on_search_timeout(self) -> None:
        if self._presenter is not None:
            self._presenter.on_search_text_changed(self._scan_input.text())

    def _on_suggestion_activated(self, item: QListWidgetItem) -> None:
        sku = item.data(Qt.ItemDataRole.UserRole)
        if self._presenter is not None and isinstance(sku, str):
            self._presenter.select_suggestion(sku)

    def _on_payment(self) -> None:
        if self._presenter is not None:
            self._presenter.begin_payment()

    def _on_discount(self) -> None:
        if self._presenter is not None:
            self._presenter.apply_discount()

    def _on_cancel_item(self) -> None:
        if self._presenter is not None:
            self._presenter.cancel_selected_item()

    def _on_cancel_sale(self) -> None:
        if self._presenter is not None:
            self._presenter.cancel_sale()

    def _on_escape(self) -> None:
        if self._presenter is not None:
            self._presenter.on_escape()
        else:
            self.close()

    # --- PosView ------------------------------------------------------------

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "PDV", message)

    def set_operator(self, username: str) -> None:
        self._operator_label.setText(f"Operador: {username or '—'}")

    def set_items(self, rows: list[PosItemRow]) -> None:
        self._items_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            description = QTableWidgetItem(row.description)
            description.setData(Qt.ItemDataRole.UserRole, row.item_id)
            quantity = QTableWidgetItem(_format_quantity(row.quantity_thousandths))
            unit = QTableWidgetItem(row.unit)
            price = QTableWidgetItem(Money(row.unit_price_cents).format_brl())
            total = QTableWidgetItem(Money(row.line_total_cents).format_brl())
            for column, cell in enumerate((description, quantity, unit, price, total)):
                self._items_table.setItem(row_index, column, cell)

    def set_totals(self, *, subtotal_cents: int, discount_cents: int, total_cents: int) -> None:
        self._subtotal_label.setText(f"Subtotal: {Money(subtotal_cents).format_brl()}")
        self._discount_label.setText(f"Desconto: {Money(discount_cents).format_brl()}")
        self._total_label.setText(Money(total_cents).format_brl())

    def set_suggestions(self, options: list[ProductOption]) -> None:
        self._suggestions.clear()
        for option in options:
            label = f"{option.name}  ({option.sku})  {Money(option.price_cents).format_brl()}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, option.sku)
            self._suggestions.addItem(item)
        self._suggestions.setVisible(bool(options))

    def clear_scan_input(self) -> None:
        self._scan_input.clear()

    def focus_scan_input(self) -> None:
        self._scan_input.setFocus()

    def get_scan_input(self) -> str:
        return self._scan_input.text()

    def get_selected_item_id(self) -> int | None:
        row = self._items_table.currentRow()
        if row < 0:
            return None
        cell = self._items_table.item(row, 0)
        if cell is None:
            return None
        data = cell.data(Qt.ItemDataRole.UserRole)
        return data if isinstance(data, int) else None

    def ask_payment(self, total_cents: int) -> list[PaymentEntry] | None:
        return PaymentDialog.ask(total_cents, self)

    def ask_discount(self, current_total_cents: int) -> int | None:
        value, ok = QInputDialog.getInt(
            self,
            "Desconto",
            "Desconto em centavos:",
            0,
            0,
            max(0, current_total_cents),
            100,
        )
        return value if ok else None

    def ask_supervisor_credentials(self) -> tuple[str, str] | None:
        return PinDialog.ask(self)

    def ask_cancel_reason(self) -> str | None:
        text, ok = QInputDialog.getText(self, "Cancelamento", "Motivo do cancelamento:")
        if not ok:
            return None
        reason = text.strip()
        return reason or None

    def show_sale_finalized(self, *, sale_id: int, total_cents: int, change_cents: int) -> None:
        message = f"Venda {sale_id} finalizada.\nTotal: {Money(total_cents).format_brl()}"
        if change_cents > 0:
            message += f"\nTroco: {Money(change_cents).format_brl()}"
        QMessageBox.information(self, "Venda finalizada", message)

    def close_view(self) -> None:
        self.close()


def create_pos_dialog(
    *,
    sales_services: SalesServices,
    identity_services: IdentityServices,
    session: CurrentSession,
    session_id: int | None = None,
    parent: QWidget | None = None,
) -> PosDialog:
    """Cria a tela do PDV, injeta o presenter e inicia uma venda."""
    dialog = PosDialog(None, session, session_id, parent)
    presenter = PosPresenter(
        view=dialog,
        sales_services=sales_services,
        identity_services=identity_services,
        session=session,
        session_id=session_id,
    )
    dialog.set_presenter(presenter)
    presenter.start()
    return dialog
