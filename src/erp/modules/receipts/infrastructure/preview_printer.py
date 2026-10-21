"""Preview printer — shows receipt in a QTextEdit dialog for preview."""

from __future__ import annotations

from erp.modules.receipts.application.formatter import ReceiptFormatter
from erp.modules.receipts.application.ports import ReceiptPrinterPort
from erp.modules.receipts.domain import Receipt


class PreviewPrinter(ReceiptPrinterPort):
    """Preview printer that shows the receipt in a QDialog with QTextEdit."""

    def __init__(self, width: int = 48) -> None:
        self._formatter = ReceiptFormatter(width=width)

    def print_receipt(self, receipt: Receipt) -> None:
        from PySide6.QtGui import QFontDatabase
        from PySide6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
        )

        formatter = ReceiptFormatter(width=48)
        text = formatter.format_receipt(receipt)

        dialog: QDialog = QDialog()
        dialog.setWindowTitle("Pré-visualização do Cupom")
        dialog.setModal(True)
        dialog.resize(500, 700)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Use monospace font
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)

        text_edit.setFont(font)
        text_edit.setPlainText(text)
        layout = QVBoxLayout()
        layout.addWidget(text_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        print_btn = QPushButton("Imprimir")
        print_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(print_btn)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(close_btn)

        layout = QVBoxLayout(dialog)
        layout.addWidget(text_edit)
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def open_cash_drawer(self) -> None:
        # Preview printer doesn't open cash drawer
        pass
