"""Receipt preview dialog and print service."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from erp.modules.receipts.application.formatter import ReceiptFormatter
from erp.modules.receipts.domain import Receipt


class ReceiptPreviewDialog(QDialog):
    """Dialog for previewing a receipt before printing."""

    def __init__(
        self,
        receipt: Receipt,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._receipt = receipt
        self._formatter = ReceiptFormatter(width=48)

        self.setWindowTitle("Pré-visualização do Cupom")
        self.setModal(True)
        self.resize(500, 700)

        self._setup_ui()
        self._load_receipt()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Use monospace font
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)
        self._text_edit.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self._text_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._print_btn = QPushButton("Imprimir")
        self._print_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._print_btn)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_receipt(self) -> None:
        formatter = ReceiptFormatter(width=48)
        text = formatter.format_receipt(self._receipt)
        self._text_edit.setPlainText(text)

    def get_receipt_text(self) -> str:
        """Returns the formatted receipt text."""
        formatter = ReceiptFormatter(width=48)
        return formatter.format_receipt(self._receipt)