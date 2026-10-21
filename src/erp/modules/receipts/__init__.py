"""Receipts module — non-fiscal receipt generation and printing."""

from erp.modules.receipts.application import (
    CompanySettingsPort,
    ReceiptFormatter,
    ReceiptGenerator,
    ReceiptPrinterPort,
    ReceiptRepositoryPort,
)
from erp.modules.receipts.domain import Receipt, ReceiptLine
from erp.modules.receipts.presentation import PrinterSettingsDialog, ReceiptPreviewDialog

__all__ = [
    "CompanySettingsPort",
    "PrinterSettingsDialog",
    "Receipt",
    "ReceiptFormatter",
    "ReceiptGenerator",
    "ReceiptLine",
    "ReceiptPreviewDialog",
    "ReceiptPrinterPort",
    "ReceiptRepositoryPort",
]
