"""Diálogo de autorização do supervisor (usuário + senha/PIN)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_logger = logging.getLogger(__name__)


def _load_theme_qss() -> str:
    """Carrega o arquivo QSS do design system."""
    qss_path = Path(__file__).resolve().parent.parent.parent.parent / "shared" / "ui" / "theme.qss"
    try:
        return qss_path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - fallback silencioso
        _logger.warning("Falha ao carregar stylesheet: %s", exc)
        return ""


class PinDialog(QDialog):
    """Coleta as credenciais do supervisor; a validação fica no presenter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Autorização do supervisor")
        self.setModal(True)
        self.resize(360, 170)
        self.setStyleSheet(_load_theme_qss())

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._username = QLineEdit()
        self._username.setPlaceholderText("Usuário do supervisor")
        self._username.setAccessibleName("Usuário do supervisor")
        form.addRow("Usuário:", self._username)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("PIN ou senha do supervisor")
        self._password.setAccessibleName("PIN ou senha do supervisor")
        form.addRow("PIN/senha:", self._password)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setObjectName("btnPrimary")
            ok_button.setText("Autorizar")
            ok_button.setDefault(True)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setObjectName("btnSecondary")
            cancel_button.setText("Cancelar")
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
