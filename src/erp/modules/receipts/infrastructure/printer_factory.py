"""Printer factory — selects and configures the appropriate printer adapter."""

from __future__ import annotations

import sys
from typing import TypedDict

from erp.modules.receipts.infrastructure.cups_printer import CupsPrinter
from erp.modules.receipts.infrastructure.escpos_printer import EscposPrinter
from erp.modules.receipts.infrastructure.preview_printer import PreviewPrinter


class PreviewConfig(TypedDict, total=False):
    width: int


class EscposConfig(TypedDict, total=False):
    device_path: str
    width: int
    profile: str


class CupsConfig(TypedDict, total=False):
    printer_name: str
    width: int


class WindowsSpoolerConfig(TypedDict, total=False):
    printer_name: str
    width: int


class PrinterSettings(TypedDict, total=False):
    printer_type: str
    device_path: str
    profile: str
    printer_name: str
    cups_printer: str
    win_printer: str
    width: int


class PrinterFactory:
    """Factory for creating printer instances based on configuration."""

    def __init__(self) -> None:
        self._printer = None

    def create_printer(
        self,
        printer_type: str,
        config: dict[str, object],
        width: int = 48,
    ) -> object:
        """Creates a printer instance based on type and configuration."""
        if printer_type == "preview":
            return PreviewPrinter(width=config.get("width", 48))  # type: ignore[arg-type]
        if printer_type == "escpos":
            return EscposPrinter(
                device_path=config.get("device_path", "/dev/usb/lp0"),
                width=config.get("width", 48),
                profile=config.get("profile", "default"),
            )  # type: ignore[arg-type]
        if printer_type == "cups":
            if sys.platform == "win32":
                raise RuntimeError("CUPS printer not available on Windows")
            return CupsPrinter(
                printer_name=config.get("printer_name", "default"),
                width=config.get("width", 48),
            )  # type: ignore[arg-type]
        if printer_type == "windows_spooler":
            if sys.platform != "win32":
                raise RuntimeError("Windows spooler only available on Windows")
            try:
                from erp.modules.receipts.infrastructure.windows_spooler import (
                    WindowsSpoolerPrinter,
                )
            except ImportError as exc:
                raise RuntimeError("win32print not available") from exc
            return WindowsSpoolerPrinter(
                printer_name=config.get("printer_name", ""),
                width=config.get("width", 48),
            )  # type: ignore[arg-type]
        raise ValueError(f"Unknown printer type: {printer_type}")

    def create_from_settings(self, settings: dict[str, object]) -> object:
        """Creates printer from settings dict."""
        printer_type = settings.get("printer_type", "preview")
        return self.create_printer(printer_type, settings)  # type: ignore[arg-type]
