"""Windows RAW spooler printer adapter."""

from __future__ import annotations

import sys
from typing import Any

from erp.modules.receipts.application.formatter import ReceiptFormatter
from erp.modules.receipts.application.ports import ReceiptPrinterPort
from erp.modules.receipts.domain import Receipt


class WindowsSpoolerPrinter(ReceiptPrinterPort):
    """Windows RAW spooler printer adapter using win32print."""

    def __init__(self, printer_name: str, width: int = 48) -> None:
        if sys.platform != "win32":
            raise RuntimeError("WindowsSpoolerPrinter only works on Windows")
        self._printer_name: str = printer_name
        self._formatter = ReceiptFormatter(width=48)

    def print_receipt(self, receipt: Receipt) -> None:
        import win32print  # type: ignore[import-untyped,import-not-found]

        formatter = ReceiptFormatter(width=48)
        text = formatter.format_receipt(receipt)

        # Get printer handle
        printer_handle: Any = win32print.OpenPrinter(self._printer_name)
        try:
            # Start document
            job_info: tuple[str, None, str] = ("NexoERP Receipt", None, "RAW")
            win32print.StartDocPrinter(printer_handle, 1, job_info)
            win32print.StartPagePrinter(printer_handle)

            # Write raw data
            data = text.encode("cp1252", errors="replace")
            win32print.WritePrinter(printer_handle, data)

            # Cut paper (ESC/POS cut command)
            cut_command = b"\x1d\x56\x00"  # ESC/POS cut
            win32print.WritePrinter(printer_handle, cut_command)

            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
        finally:
            win32print.ClosePrinter(printer_handle)

    def open_cash_drawer(self) -> None:
        import win32print  # type: ignore[import-untyped,import-not-found]

        printer_handle: Any = win32print.OpenPrinter(self._printer_name)
        try:
            job_info: tuple[str, None, str] = ("NexoERP Cash Drawer", None, "RAW")
            win32print.StartDocPrinter(printer_handle, 1, job_info)
            win32print.StartPagePrinter(printer_handle)

            # Cash drawer kick command (ESC/POS)
            kick_command = b"\x1b\x70\x00\x19\xfa"  # ESC p 0 25 250
            win32print.WritePrinter(printer_handle, kick_command)

            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
        finally:
            win32print.ClosePrinter(printer_handle)
