"""Qt view for company settings."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.settings.application.services import SettingsServices
from erp.modules.settings.presentation.settings_presenter import (
    SettingsPresenter,
    SettingsView,
)
from erp.shared.application.session import CurrentSession


class SettingsDialog(QDialog, SettingsView):
    """Diálogo de configurações da empresa."""

    def __init__(
        self,
        presenter: SettingsPresenter | None,
        session: CurrentSession,
        company_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session

        self.setWindowTitle("Configurações da Empresa")
        self.setModal(True)
        self.resize(520, 520)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._company_name = QLineEdit()
        self._company_name.setPlaceholderText("Nome da empresa")
        form.addRow("Nome da empresa:", self._company_name)

        self._cnpj = QLineEdit()
        self._cnpj.setPlaceholderText("00.000.000/0001-00")
        form.addRow("CNPJ (opcional):", self._cnpj)

        self._address = QLineEdit()
        self._address.setPlaceholderText("Endereço")
        form.addRow("Endereço:", self._address)

        self._receipt_header = QLineEdit()
        self._receipt_header.setPlaceholderText("Mensagem no cabeçalho do cupom")
        form.addRow("Cabeçalho do cupom:", self._receipt_header)

        self._receipt_footer = QLineEdit()
        self._receipt_footer.setPlaceholderText("Mensagem no rodapé do cupom")
        form.addRow("Rodapé do cupom:", self._receipt_footer)

        self._idle_timeout = QSpinBox()
        self._idle_timeout.setRange(1, 480)
        self._idle_timeout.setSuffix(" minutos")
        self._idle_timeout.setValue(30)
        form.addRow("Timeout de sessão ociosa:", self._idle_timeout)

        layout.addLayout(form)

        # Hint
        hint = QLabel("Esses dados aparecem no cabeçalho e rodapé do cupom de venda.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Salvar")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_save_clicked(self) -> None:
        if self._presenter is not None:
            self._presenter.save_settings()

    # --- SettingsView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def show_success(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)

    def set_company_name(self, name: str) -> None:
        self._company_name.setText(name)

    def set_cnpj(self, cnpj: str) -> None:
        self._cnpj.setText(cnpj)

    def set_address(self, address: str) -> None:
        self._address.setText(address)

    def set_receipt_header(self, message: str) -> None:
        self._receipt_header.setText(message)

    def set_receipt_footer(self, message: str) -> None:
        self._receipt_footer.setText(message)

    def set_idle_timeout_minutes(self, minutes: int) -> None:
        self._idle_timeout.setValue(minutes)

    def get_company_name(self) -> str:
        return self._company_name.text().strip()

    def get_cnpj(self) -> str:
        return self._cnpj.text().strip()

    def get_address(self) -> str:
        return self._address.text().strip()

    def get_receipt_header(self) -> str:
        return self._receipt_header.text().strip()

    def get_receipt_footer(self) -> str:
        return self._receipt_footer.text().strip()

    def get_idle_timeout_minutes(self) -> int:
        return self._idle_timeout.value()

    def accept(self) -> None:
        super().accept()


def create_settings_dialog(
    services: SettingsServices,
    session: CurrentSession,
    company_name: str,
    engine: Engine,
    parent: QWidget | None = None,
) -> SettingsDialog:
    """Factory para criar o diálogo com presenter injetado."""
    dialog = SettingsDialog(None, session, company_name, parent)
    presenter = SettingsPresenter(
        view=dialog,
        services=services,
        session=session,
        company_name=company_name,
    )
    dialog._presenter = presenter
    return dialog
