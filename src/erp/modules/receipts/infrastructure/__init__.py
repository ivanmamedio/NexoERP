"""Infrastructure implementation for receipts module."""

from erp.modules.receipts.infrastructure.cups_printer import CupsPrinter
from erp.modules.receipts.infrastructure.escpos_printer import EscposPrinter
from erp.modules.receipts.infrastructure.preview_printer import PreviewPrinter
from erp.modules.receipts.infrastructure.printer_factory import PrinterFactory
from erp.modules.receipts.infrastructure.windows_spooler import WindowsSpoolerPrinter

__all__ = [
    "CupsPrinter",
    "EscposPrinter",
    "PreviewPrinter",
    "PrinterFactory",
    "WindowsSpoolerPrinter",
]
