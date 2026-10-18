"""View for creating/editing companies (Qt interface)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from erp.modules.companies.domain.company import Company
from erp.modules.companies.presentation.create_company_presenter import (
    CompaniesCreatePresenter,
)


class CompaniesCreateWidget(QDialog):
    """Dialogo de nova/edição de empresa (apenas renderização e eventos)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: CompaniesCreatePresenter | None = None

        self.setWindowTitle("Nova Empresa")
        self.setModal(True)

        self._name = QLineEdit(self)
        self._name.setPlaceholderText("Razão social")

        self._trade_name = QLineEdit(self)
        self._trade_name.setPlaceholderText("Nome fantasia")

        self._tax_id = QLineEdit(self)
        self._tax_id.setPlaceholderText("CNPJ")

        self._address = QLineEdit(self)
        self._address.setPlaceholderText("Endereço")

        self._phone = QLineEdit(self)
        self._phone.setPlaceholderText("Telefone")

        self._email = QLineEdit(self)
        self._email.setPlaceholderText("E-mail")

        self._active = QLineEdit(self)
        self._active.setPlaceholderText("Ativa (sim/não)")

        self._error = QLabel(self)
        self._error.setWordWrap(True)
        self._error.setStyleSheet("color: #c0392b;")
        self._error.hide()

        form = QFormLayout()
        form.addRow("Razão social:", self._name)
        form.addRow("Nome fantasia:", self._trade_name)
        form.addRow("CNPJ:", self._tax_id)
        form.addRow("Endereço:", self._address)
        form.addRow("Telefone:", self._phone)
        form.addRow("E-mail:", self._email)
        form.addRow("Ativa:", self._active)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Salvar")
        buttons.accepted.connect(self._on_submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._error)
        layout.addWidget(buttons)

        self._tax_id.setFocus()

    def set_presenter(self, presenter: CompaniesCreatePresenter) -> None:
        self._presenter = presenter

    def _on_submit(self) -> None:
        if self._presenter is None:
            return
        self._error.hide()
        self._presenter.save(
            name=self._name.text().strip(),
            trade_name=self._trade_name.text().strip(),
            tax_id=self._tax_id.text().strip(),
            address=self._address.text().strip(),
            phone=self._phone.text().strip(),
            email=self._email.text().strip(),
            active=self._active.text().strip().lower() in {"1", "true", "sim", "s", "sim "},
        )

    def load_company(self, company: Company | None) -> None:
        if company is None:
            self.setWindowTitle("Nova Empresa")
            self._name.clear()
            self._trade_name.clear()
            self._tax_id.clear()
            self._address.clear()
            self._phone.clear()
            self._email.clear()
            self._active.clear()
            return
        self.setWindowTitle(f"Editar empresa - {company.name}")
        self._name.setText(company.name)
        self._trade_name.setText(company.trade_name)
        self._tax_id.setText(company.tax_id)
        self._address.setText(company.address or "")
        self._phone.setText(company.phone or "")
        self._email.setText(company.email or "")
        self._active.setText("sim" if company.active else "não")
