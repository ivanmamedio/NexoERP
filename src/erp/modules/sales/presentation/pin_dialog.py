"""Diálogo de autorização do supervisor (usuário + senha/PIN)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class PinDialog(QDialog):
    """Coleta as credenciais do supervisor; a validação fica no presenter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Autorização do supervisor")
        self.setModal(True)
        self.resize(360, 170)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._username = QLineEdit()
        self._username.setPlaceholderText("Usuário do supervisor")
        form.addRow("Usuário:", self._username)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("PIN ou senha do supervisor")
        form.addRow("PIN/senha:", self._password)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._username.setFocus()

    def credentials(self) -> tuple[str, str]:
        return self._username.text().strip(), self._password.text()

    @classmethod
    def ask(cls, parent: QWidget | None = None) -> tuple[str, str] | None:
        dialog = cls(parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        username, password = dialog.credentials()
        if not username or not password:
            return None
        return username, password


def create_pin_dialog(parent: QWidget | None = None) -> PinDialog:
    return PinDialog(parent)
