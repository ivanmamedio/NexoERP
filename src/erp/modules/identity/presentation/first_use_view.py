"""Tela de primeiro uso (Qt). Cria o primeiro administrador do sistema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from erp.modules.identity.presentation.first_use_presenter import (
        FirstUsePresenter,
    )


class FirstUseDialog(QDialog):
    """Janela modal de primeiro uso: cria o primeiro administrador."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: FirstUsePresenter | None = None

        self.setWindowTitle("NexoERP — Primeiro Uso")
        self.setModal(True)
        self.setFixedSize(480, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("FirstUseDialog")
        self.setStyleSheet(_QSS)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 28, 28, 28)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget(self)
        card.setObjectName("FirstUseCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        title = QLabel("Primeiro Uso", card)
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Crie o primeiro administrador do NexoERP.", card)
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        hint = QLabel(
            "A senha deve ter no mínimo 8 caracteres, com pelo menos uma letra e um dígito.",
            card,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 12px;")
        card_layout.addWidget(hint)

        self._username = QLineEdit(card)
        self._username.setObjectName("UsernameInput")
        self._username.setPlaceholderText("Usuário (ex: admin)")
        card_layout.addWidget(self._username)

        self._password = QLineEdit(card)
        self._password.setObjectName("PasswordInput")
        self._password.setPlaceholderText("Nova senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self._password)

        self._confirm = QLineEdit(card)
        self._confirm.setObjectName("ConfirmPasswordInput")
        self._confirm.setPlaceholderText("Confirmar senha")
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self._confirm)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(14)
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)
        form.addRow("Confirmar:", self._confirm)
        card_layout.addLayout(form)

        self._error_label = QLabel(card)
        self._error_label.setObjectName("ErrorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()
        card_layout.addWidget(self._error_label)

        self._info_label = QLabel(card)
        self._info_label.setObjectName("InfoLabel")
        self._info_label.setWordWrap(True)
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.hide()
        card_layout.addWidget(self._info_label)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, card)
        self._buttons.setObjectName("CreateButtons")
        submit_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if submit_button is not None:
            submit_button.setObjectName("CreateButton")
            submit_button.setText("Criar Primeiro Administrador")
            submit_button.setDefault(True)

        self._buttons.accepted.connect(self._on_submit)
        card_layout.addWidget(self._buttons, alignment=Qt.AlignmentFlag.AlignCenter)

        root_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    # --- FirstUseView protocol ---------------------------------------

    def set_presenter(self, presenter: FirstUsePresenter) -> None:
        self._presenter = presenter

    def show_error(self, message: str) -> None:
        self._info_label.hide()
        self._error_label.setText(message)
        self._error_label.show()

    def show_info(self, message: str) -> None:
        self._error_label.hide()
        self._info_label.setText(message)
        self._info_label.show()

    def clear_passwords(self) -> None:
        self._password.clear()
        self._confirm.clear()
        self._password.setFocus()

    def accept(self) -> None:
        super().accept()

    # --- internals ----------------------------------------------------------

    def _on_submit(self) -> None:
        if self._presenter is None:
            return
        self._error_label.hide()
        self._presenter.create_first_user(
            self._username.text(),
            self._password.text(),
            self._confirm.text(),
        )


_QSS = """
QDialog#FirstUseDialog {
    background-color: #f4f6f8;
}
QLabel {
    color: #2c3e50;
}
QWidget#FirstUseCard {
    background-color: #ffffff;
    border: 1px solid #e1e5e8;
    border-radius: 12px;
}
QLineEdit#UsernameInput,
QLineEdit#PasswordInput,
QLineEdit#ConfirmPasswordInput {
    padding: 8px 10px;
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    background-color: #ffffff;
    color: #2c3e50;
    min-height: 40px;
}
QLineEdit#UsernameInput:focus,
QLineEdit#PasswordInput:focus,
QLineEdit#ConfirmPasswordInput:focus {
    border: 2px solid #3498db;
}
QPushButton#CreateButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 9px 24px;
    font-size: 14px;
    font-weight: 600;
    min-width: 120px;
    min-height: 40px;
}
QPushButton#CreateButton:hover {
    background-color: #2980b9;
}
QPushButton#CreateButton:pressed {
    background-color: #1f618d;
}
QLabel#ErrorLabel {
    color: #c0392b;
    font-size: 12px;
}
QLabel#InfoLabel {
    color: #27ae60;
    font-size: 12px;
}
QLabel#TitleLabel {
    font-size: 22px;
    font-weight: 600;
    color: #2c3e50;
}
QLabel#SubtitleLabel {
    font-size: 12px;
    color: #7f8c8d;
}
"""
