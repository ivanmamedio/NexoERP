"""CUPS printer adapter for Linux."""

from __future__ import annotations

import subprocess
import sys

from erp.modules.receipts.application.formatter import ReceiptFormatter
from erp.modules.receipts.application.ports import ReceiptPrinterPort
from erp.modules.receipts.domain import Receipt


class CupsPrinter(ReceiptPrinterPort):
    """CUPS printer adapter using lp command."""

    def __init__(self, printer_name: str, width: int = 48) -> None:
        if sys.platform == "win32":
            raise RuntimeError("CUPS printer only works on Linux/Unix")
        self._printer_name = printer_name
        self._formatter = ReceiptFormatter(width=48)

    def print_receipt(self, receipt: Receipt) -> None:
        formatter = ReceiptFormatter(width=48)
        text = formatter.format_receipt(receipt)

        # Use lp command to print
        # -d specifies printer, -o raw sends raw data
        proc = subprocess.run(
            ["lp", "-d", self._printer_name, "-o", "raw"],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"CUPS print failed: {proc.stderr.decode()}")

    def open_cash_drawer(self) -> None:
        # Cash drawer kick via CUPS - send raw ESC/POS command
        kick_command = b"\x1b\x70\x00\x19\xfa"  # ESC p 0 25 250
        proc = subprocess.run(
            ["lp", "-d", self._printer_name, "-o", "raw"],
            input=kick_command,
            capture_output=True,
            timeout=10,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"CUPS cash drawer failed: {proc.stderr.decode()}")
