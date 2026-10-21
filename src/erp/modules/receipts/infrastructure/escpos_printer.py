"""ESC/POS printer adapter using python-escpos."""

from __future__ import annotations

from erp.modules.receipts.application.formatter import ReceiptFormatter
from erp.modules.receipts.application.ports import ReceiptPrinterPort


class EscposPrinter(ReceiptPrinterPort):
    """ESC/POS printer adapter using python-escpos."""

    def __init__(
        self,
        device_path: str = "/dev/usb/lp0",
        width: int = ReceiptFormatter.WIDTH_80MM,
        profile: str = "default",
    ) -> None:
        self._device_path = device_path
        self._formatter = ReceiptFormatter(width=width)
        self._profile = profile
        self._printer = None

    def _get_printer(self):
        """Lazy initialization of the printer."""
        if self._printer is None:
            try:
                from escpos.printer import File, Network, Serial, Usb
            except ImportError as exc:
                raise RuntimeError(
                    "python-escpos not installed. Run: uv add python-escpos"
                ) from exc

            # Try different connection types based on device_path
            if self._device_path.startswith("tcp://"):
                # Network printer: tcp://host:port
                host_port = self._device_path[6:]
                host, port = host_port.split(":") if ":" in host_port else (host_port, 9100)
                self._printer = Network(host, int(port))
            elif self._device_path.startswith("serial://"):
                # Serial printer: serial:///dev/ttyUSB0:9600
                serial_path = self._device_path[9:]
                port, baudrate = (
                    serial_path.split(":") if ":" in serial_path else (serial_path, 9600)
                )
                self._printer = Serial(port, baudrate=int(baudrate))
            elif self._device_path.startswith("file://"):
                # File output (for testing)
                file_path = self._device_path[7:]
                self._printer = File(file_path)
            else:
                # USB printer (default)
                vendor_id = 0x0416
                product_id = 0x5011

                if ":" in self._device_path:
                    vendor_str, product_str = self._device_path.split(":")
                    v_id = int(vendor_str, 16) if vendor_str.startswith("0x") else int(vendor_str)
                    p_id = (
                        int(product_str, 16) if product_str.startswith("0x") else int(product_str)
                    )
                    vendor_id = v_id
                    product_id = p_id

                from escpos.printer import Usb

                self._printer = Usb(vendor_id, product_id, profile=self._profile)
        return self._printer

    def print_receipt(self, receipt) -> None:
        printer = self._get_printer()
        formatter = ReceiptFormatter(width=48)  # 80mm default
        text = formatter.format_receipt(receipt)

        # Print using escpos
        printer.text(text)
        printer.cut()

    def open_cash_drawer(self) -> None:
        printer = self._get_printer()
        # Standard cash drawer kick command (pin 2 or 5)
        printer.cashdraw(2)
