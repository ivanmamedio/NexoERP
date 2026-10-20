"""Diálogo de pagamento misto do PDV (dinheiro, Pix e cartão)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from erp.modules.sales.presentation.pos_presenter import PaymentEntry
from erp.shared.domain.value_objects import Money


class PaymentDialog(QDialog):
    """Coleta os valores por meio de pagamento e mostra o troco em tempo real."""

    def __init__(self, total_cents: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._total_cents = total_cents
        self._payments: list[PaymentEntry] | None = None

        self.setWindowTitle("Pagamento")
        self.setModal(True)
        self.resize(380, 300)

        layout = QVBoxLayout(self)

        total_label = QLabel(f"Total: {Money(total_cents).format_brl()}")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(total_label)

        form = QFormLayout()
        self._cash_spin = self._make_spin(total_cents)
        self._pix_spin = self._make_spin(0)
        self._card_spin = self._make_spin(0)
        form.addRow("Dinheiro:", self._cash_spin)
        form.addRow("Pix:", self._pix_spin)
        form.addRow("Cartão:", self._card_spin)
        layout.addLayout(form)

        self._summary_label = QLabel()
        self._summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._summary_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self._summary_label)

        hint = QLabel("Zere o dinheiro para pagamento misto.")
        hint.setStyleSheet("color: gray;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self._clear_values)
        buttons.addWidget(clear_button)
        buttons.addStretch()
        cancel_button = QPushButton("Cancelar (Esc)")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)
        self._confirm_button = QPushButton("Confirmar (Enter)")
        self._confirm_button.setDefault(True)
        self._confirm_button.clicked.connect(self._on_confirm)
        buttons.addWidget(self._confirm_button)
        layout.addLayout(buttons)

        for spin in (self._cash_spin, self._pix_spin, self._card_spin):
            spin.valueChanged.connect(self._update_summary)
        self._update_summary()
        self._cash_spin.setFocus()
        self._cash_spin.selectAll()

    @staticmethod
    def _make_spin(value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 99_999_999)
        spin.setSuffix(" centavos")
        spin.setGroupSeparatorShown(True)
        spin.setValue(value)
        return spin

    def _clear_values(self) -> None:
        self._cash_spin.setValue(0)
        self._pix_spin.setValue(0)
        self._card_spin.setValue(0)

    def _values(self) -> list[PaymentEntry]:
        entries: list[PaymentEntry] = []
        for method, spin in (
            ("cash", self._cash_spin),
            ("pix", self._pix_spin),
            ("card", self._card_spin),
        ):
            if spin.value() > 0:
                entries.append(PaymentEntry(method=method, amount_cents=spin.value()))
        return entries

    def _update_summary(self) -> None:
        paid = sum(spin.value() for spin in (self._cash_spin, self._pix_spin, self._card_spin))
        change = paid - self._total_cents
        parts = [f"Pago: {Money(paid).format_brl()}"]
        if change > 0:
            parts.append(f"Troco: {Money(change).format_brl()}")
        elif change < 0:
            parts.append(f"Falta: {Money(-change).format_brl()}")
        self._summary_label.setText("  |  ".join(parts))
        self._summary_label.setStyleSheet(
            "font-size: 16px; color: #b40404;" if change < 0 else "font-size: 16px; color: #0b7a31;"
        )

    def _on_confirm(self) -> None:
        entries = self._values()
        paid = sum(entry.amount_cents for entry in entries)
        if paid < self._total_cents:
            QMessageBox.warning(self, "Pagamento", "Valor pago é insuficiente.")
            return
        change = paid - self._total_cents
        cash = sum(entry.amount_cents for entry in entries if entry.method == "cash")
        if change > 0 and cash < change:
            QMessageBox.warning(self, "Pagamento", "O troco só pode ser dado em dinheiro.")
            return
        self._payments = entries
        self.accept()

    def payments(self) -> list[PaymentEntry]:
        """Pagamentos confirmados (lista vazia se o diálogo foi cancelado)."""
        return list(self._payments or [])

    @classmethod
    def ask(cls, total_cents: int, parent: QWidget | None = None) -> list[PaymentEntry] | None:
        dialog = cls(total_cents, parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.payments()


def create_payment_dialog(total_cents: int, parent: QWidget | None = None) -> PaymentDialog:
    return PaymentDialog(total_cents, parent)
