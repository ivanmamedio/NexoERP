"""Tela de login (Qt). Não contém regra de negócio — delega ao presenter."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from erp.modules.identity.presentation.login_presenter import LoginPresenter


class LoginDialog(QDialog):
    """Janela modal de login (usuário + senha)."""

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)

        self._username = QLineEdit(self)
        self._username.setPlaceholderText("Usuário")
        self._password = QLineEdit(self)
        self._password.setPlaceholderText("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)

        self._error_label = QLabel(self)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #c0392b;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Entrar")
        self._buttons.accepted.connect(self._on_submit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._error_label)
        layout.addWidget(self._buttons)

        self._password.returnPressed.connect(self._on_submit)
        self._username.setFocus()

    def set_presenter(self, presenter: LoginPresenter) -> None:
        self._presenter = presenter

    # --- LoginView protocol -------------------------------------------------

    def show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def clear_password(self) -> None:
        self._password.clear()
        self._password.setFocus()

    # --- internals ----------------------------------------------------------

    def _on_submit(self) -> None:
        if self._presenter is None:
            return
        self._error_label.hide()
        self._presenter.login(self._username.text(), self._password.text())

    def keyPressEvent(self, event: object) -> None:
        super().keyPressEvent(event)  # type: ignore[arg-type]
