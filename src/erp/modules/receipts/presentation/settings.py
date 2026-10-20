"""Printer settings dialog for configuring receipt printers."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from erp.modules.receipts.domain import Receipt
from erp.shared.domain.value_objects import Money


class PrinterSettingsDialog(QDialog):
    """Dialog for configuring receipt printer settings."""

    def __init__(
        self,
        current_settings: dict[str, object],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = current_settings.copy()

        self.setWindowTitle("Configurações de Impressora")
        self.setModal(True)
        self.resize(400, 350)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Printer type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["preview", "escpos", "cups", "windows_spooler"])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Tipo de impressora:", self._type_combo)

        # ESC/POS specific
        self._device_path = QLineEdit()
        self._device_path.setPlaceholderText("/dev/usb/lp0 ou tcp://host:port")
        form.addRow("Caminho do dispositivo (ESC/POS):", self._device_path)

        self._profile = QLineEdit()
        self._profile.setPlaceholderText("default")
        form.addRow("Perfil ESC/POS:", self._profile)

        # CUPS specific
        self._cups_printer = QLineEdit()
        self._cups_printer.setPlaceholderText("Nome da impressora CUPS")
        form.addRow("Impressora CUPS:", self._cups_printer)

        # Windows spooler specific
        self._win_printer = QLineEdit()
        self._win_printer.setPlaceholderText("Nome da impressora Windows")
        form.addRow("Impressora Windows:", self._win_printer)

        # Width
        self._width_spin = QSpinBox()
        self._width_spin.setRange(32, 48)
        self._width_spin.setSingleStep(16)
        self._width_spin.setValue(48)
        form.addRow("Largura (colunas):", self._width_spin)

        layout = QVBoxLayout()
        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._test_btn = QPushButton("Testar Impressão")
        self._test_btn.clicked.connect(self._on_test)
        btn_layout.addWidget(self._test_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _on_type_changed(self, printer_type: str) -> None:
        # Enable/disable fields based on type
        is_escpos = printer_type == "escpos"
        is_cups = printer_type == "cups"
        is_win = printer_type == "windows_spooler"

        self._device_path.setEnabled(is_escpos)
        self._profile.setEnabled(is_escpos)
        self._cups_printer.setEnabled(is_cups)
        self._win_printer.setEnabled(is_win)

    def _load_settings(self) -> None:
        self._type_combo.setCurrentText(self._settings.get("printer_type", "preview"))
        self._device_path.setText(self._settings.get("device_path", "/dev/usb/lp0"))
        self._profile.setText(self._settings.get("profile", "default"))
        self._cups_printer.setText(self._settings.get("cups_printer", ""))
        self._win_printer.setText(self._settings.get("win_printer", ""))
        self._width_spin.setValue(self._settings.get("width", 48))
        self._on_type_changed(self._settings.get("printer_type", "preview"))

    def _on_test(self) -> None:
        # Create a test receipt
        test_receipt = Receipt(
            company_name="EMPRESA TESTE LTDA",
            company_tax_id="12.345.678/0001-90",
            company_address="Rua Teste, 123 - Centro",
            company_phone="(11) 99999-9999",
            header_lines=["CUPOM NÃO FISCAL", "TESTE DE IMPRESSÃO"],
            footer_lines=["Obrigado pela preferência!", "Volte sempre!"],
            terminal_code="PDV01",
            operator_name="Operador Teste",
        )
        test_receipt.add_line("PRODUTO TESTE", 1.0, "UN", Money(1000))
        test_receipt.add_payment("DINHEIRO", Money(1000))
        test_receipt.close()

        try:
            printer_type = self._type_combo.currentText()
            settings = self._get_current_settings()
            from erp.modules.receipts.infrastructure.printer_factory import PrinterFactory
            factory = PrinterFactory()
            printer = factory.create_printer(printer_type, settings)
            printer.print_receipt(test_receipt)
            QMessageBox.information(self, "Teste", "Impressão de teste enviada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro no Teste", f"Falha na impressão de teste:\n{e}")

    def _get_current_settings(self) -> dict[str, object]:
        return {
            "printer_type": self._type_combo.currentText(),
            "device_path": self._device_path.text(),
            "profile": self._profile.text(),
            "cups_printer": self._cups_printer.text(),
            "win_printer": self._win_printer.text(),
            "width": self._width_spin.value(),
        }

    def _on_save(self) -> None:
        self._settings = self._get_current_settings()
        self.accept()

    def get_settings(self) -> dict[str, object]:
        return self._settings


def create_printer_settings_dialog(
    current_settings: dict[str, object], parent: QWidget | None = None
) -> PrinterSettingsDialog:
    return PrinterSettingsDialog(current_settings, parent)