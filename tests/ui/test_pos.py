"""Testes pytest-qt da tela do PDV (offscreen, sem exibir janela)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from erp.modules.sales.presentation.payment_dialog import PaymentDialog
from erp.modules.sales.presentation.pos_presenter import PosItemRow, ProductOption
from erp.modules.sales.presentation.pos_view import PosDialog
from erp.shared.application.session import CurrentSession


class FakePresenter:
    def __init__(self) -> None:
        self.scans = 0
        self.payments = 0
        self.discounts = 0
        self.cancel_items = 0
        self.cancel_sales = 0
        self.escapes = 0

    def on_scan_entered(self) -> bool:
        self.scans += 1
        return True

    def begin_payment(self) -> bool:
        self.payments += 1
        return True

    def apply_discount(self) -> bool:
        self.discounts += 1
        return True

    def cancel_selected_item(self) -> bool:
        self.cancel_items += 1
        return True

    def cancel_sale(self) -> bool:
        self.cancel_sales += 1
        return True

    def on_escape(self) -> None:
        self.escapes += 1


def _make_dialog(qtbot) -> tuple[PosDialog, FakePresenter]:
    presenter = FakePresenter()
    dialog = PosDialog(
        presenter,  # type: ignore[arg-type]
        CurrentSession(user_id=1, company_id=1, username="caixa"),
        session_id=1,
    )
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.activateWindow()
    return dialog, presenter


def test_scan_enter_calls_presenter(qtbot) -> None:
    dialog, presenter = _make_dialog(qtbot)

    dialog._scan_input.setText("ARROZ-5KG")
    QTest.keyClick(dialog._scan_input, Qt.Key.Key_Return)

    assert presenter.scans == 1


def test_function_keys_trigger_actions(qtbot) -> None:
    dialog, presenter = _make_dialog(qtbot)

    QTest.keyClick(dialog, Qt.Key.Key_F2)
    QTest.keyClick(dialog, Qt.Key.Key_F4)
    QTest.keyClick(dialog, Qt.Key.Key_F6)
    QTest.keyClick(dialog, Qt.Key.Key_F8)
    QTest.keyClick(dialog, Qt.Key.Key_Escape)

    assert presenter.payments == 1
    assert presenter.discounts == 1
    assert presenter.cancel_items == 1
    assert presenter.cancel_sales == 1
    assert presenter.escapes == 1


def test_items_table_and_selection(qtbot) -> None:
    dialog, _ = _make_dialog(qtbot)

    dialog.set_items(
        [
            PosItemRow(
                item_id=10,
                description="Arroz 5kg",
                quantity_thousandths=2000,
                unit="un",
                unit_price_cents=1000,
                line_total_cents=2000,
            )
        ]
    )
    dialog._items_table.selectRow(0)

    assert dialog._items_table.rowCount() == 1
    assert dialog.get_selected_item_id() == 10


def test_down_arrow_moves_to_suggestions(qtbot) -> None:
    dialog, _ = _make_dialog(qtbot)
    dialog.set_suggestions(
        [
            ProductOption(
                product_id=1,
                sku="ARROZ-5KG",
                name="Arroz 5kg",
                price_cents=1000,
                stock_qty=5000,
                unit="un",
            )
        ]
    )
    dialog._scan_input.setFocus()

    QTest.keyClick(dialog._scan_input, Qt.Key.Key_Down)

    assert dialog._suggestions.currentRow() == 0


def test_total_is_formatted_in_brl(qtbot) -> None:
    dialog, _ = _make_dialog(qtbot)

    dialog.set_totals(subtotal_cents=123456, discount_cents=456, total_cents=123000)

    assert dialog._total_label.text() == "R$ 1.230,00"


def test_payment_dialog_calculates_change(qtbot) -> None:
    dialog = PaymentDialog(total_cents=5000)
    qtbot.addWidget(dialog)

    dialog._cash_spin.setValue(10000)

    assert "Troco" in dialog._summary_label.text()
    assert "R$ 50,00" in dialog._summary_label.text()


def test_payment_dialog_rejects_insufficient_amount(qtbot, monkeypatch) -> None:
    dialog = PaymentDialog(total_cents=5000)
    qtbot.addWidget(dialog)
    dialog._cash_spin.setValue(1000)
    warnings: list[str] = []
    monkeypatch.setattr(
        "erp.modules.sales.presentation.payment_dialog.QMessageBox.warning",
        lambda *args, **kwargs: warnings.append(str(args[2])),
    )

    dialog._on_confirm()

    assert warnings
    assert dialog.payments() == []
