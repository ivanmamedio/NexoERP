"""Pricing assistant view (Qt interface)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from erp.modules.pricing.application.calculate_price import CalculatePriceOutput

if TYPE_CHECKING:
    from erp.modules.pricing.presentation.pricing_presenter import PricingPresenter


class PricingAssistantWidget(QWidget):
    """Tela assistente de precificacao com calculo em tempo real."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Precificacao")

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._cost = QDoubleSpinBox(self)
        self._cost.setDecimals(2)
        self._cost.setMaximum(999999.99)
        self._cost.setPrefix("R$ ")
        form.addRow("Custo (R$):", self._cost)

        self._tax = QDoubleSpinBox(self)
        self._tax.setDecimals(2)
        self._tax.setMaximum(100.0)
        self._tax.setSuffix(" %")
        form.addRow("Imposto (%):", self._tax)

        self._card_fee = QDoubleSpinBox(self)
        self._card_fee.setDecimals(2)
        self._card_fee.setMaximum(100.0)
        self._card_fee.setSuffix(" %")
        form.addRow("Taxa cartao (%):", self._card_fee)

        self._margin = QDoubleSpinBox(self)
        self._margin.setDecimals(2)
        self._margin.setMaximum(100.0)
        self._margin.setSuffix(" %")
        form.addRow("Margem (%):", self._margin)

        layout.addLayout(form)

        # Result labels
        self._result_price = QLabel("Preco de venda: R$ 0,00", self)
        self._result_margin = QLabel("Margem liquida: 0,00%", self)
        self._result_tax = QLabel("Imposto: R$ 0,00", self)
        self._result_card = QLabel("Taxa cartao: R$ 0,00", self)
        self._result_margin_amt = QLabel("Margem: R$ 0,00", self)

        for lbl in (
            self._result_price,
            self._result_margin,
            self._result_tax,
            self._result_card,
            self._result_margin_amt,
        ):
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(lbl)

        self._btn_apply = QPushButton("Aplicar ao produto", self)
        self._btn_apply.setEnabled(False)
        layout.addWidget(self._btn_apply)

        self._error = QLabel(self)
        self._error.setStyleSheet("color: #c0392b;")
        self._error.hide()
        layout.addWidget(self._error)

        layout.setContentsMargins(8, 8, 8, 8)

        # Wire live calculation
        for spin in (self._cost, self._tax, self._card_fee, self._margin):
            spin.valueChanged.connect(self._on_changed)

    def set_presenter(self, presenter: PricingPresenter) -> None:
        self._presenter = presenter

    def _on_changed(self) -> None:
        if self._presenter is None:
            return
        self._presenter.calculate(
            cost_cents=int(self._cost.value() * 100),
            tax_pct_hundredths=int(self._tax.value() * 100),
            card_fee_pct_hundredths=int(self._card_fee.value() * 100),
            margin_pct_hundredths=int(self._margin.value() * 100),
        )

    def show_result(self, output: CalculatePriceOutput) -> None:
        self._error.hide()
        self._btn_apply.setEnabled(True)
        self._result_price.setText(
            f"Preco de venda: R$ {output.sale_price_cents / 100:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        self._result_margin.setText(
            f"Margem liquida: {output.net_margin_pct_hundredths / 100:.2f}%"
        )
        self._result_tax.setText(
            f"Imposto: R$ {output.tax_amount_cents / 100:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        self._result_card.setText(
            f"Taxa cartao: R$ {output.card_fee_amount_cents / 100:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        self._result_margin_amt.setText(
            f"Margem: R$ {output.margin_amount_cents / 100:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        self._btn_apply.setEnabled(True)

    def show_error(self, message: str) -> None:
        self._error.setText(message)
        self._error.show()
        self._btn_apply.setEnabled(False)

    def set_product_id(self, product_id: int | None) -> None:
        self._product_id = product_id

    def get_product_id(self) -> int | None:
        return getattr(self, "_product_id", None)
