"""Tela de troca de senha (Qt). Delega ao ChangePasswordPresenter."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from erp.modules.identity.presentation.change_password_presenter import ChangePasswordPresenter


class ChangePasswordDialog(QDialog):
    """Janela modal de troca de senha (self-service ou forçada)."""

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._presenter: ChangePasswordPresenter | None = None

        self.setWindowTitle("NexoERP — Alterar Senha")
        self.setModal(True)

        self._current = QLineEdit(self)
        self._current.setEchoMode(QLineEdit.EchoMode.Password)
        self._new = QLineEdit(self)
        self._new.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm = QLineEdit(self)
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        self._current_row_label = QLabel("Senha atual:")
        form.addRow(self._current_row_label, self._current)
        form.addRow("Nova senha:", self._new)
        form.addRow("Confirmar nova senha:", self._confirm)

        hint = QLabel(
            "A senha deve ter no mínimo 8 caracteres, com pelo menos uma letra e um dígito.",
            self,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666;")

        self._error_label = QLabel(self)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #c0392b;")
        self._error_label.hide()

        self._info_label = QLabel(self)
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #27ae60;")
        self._info_label.hide()

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Salvar")
        self._buttons.accepted.connect(self._on_submit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(self._error_label)
        layout.addWidget(self._info_label)
        layout.addWidget(self._buttons)

        self._confirm.returnPressed.connect(self._on_submit)

    def set_presenter(self, presenter: ChangePasswordPresenter) -> None:
        self._presenter = presenter

    # --- ChangePasswordView protocol ---------------------------------------

    def show_error(self, message: str) -> None:
        self._info_label.hide()
        self._error_label.setText(message)
        self._error_label.show()

    def show_info(self, message: str) -> None:
        self._error_label.hide()
        self._info_label.setText(message)
        self._info_label.show()

    def clear_passwords(self) -> None:
        self._new.clear()
        self._confirm.clear()
        self._new.setFocus()

    def set_require_current(self, required: bool) -> None:
        self._current.setVisible(required)
        self._current_row_label.setVisible(required)

    # --- internals ----------------------------------------------------------

    def _on_submit(self) -> None:
        if self._presenter is None:
            return
        self._error_label.hide()
        self._presenter.change(self._current.text(), self._new.text(), self._confirm.text())
