"""Tela de login (Qt). Não contém regra de negócio — delega ao presenter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from erp.ui.resource_paths import resource_path

if TYPE_CHECKING:
    from erp.modules.identity.presentation.login_presenter import LoginPresenter

logger = logging.getLogger(__name__)

# Estilo único por objectName (definido em um único lugar).
_QSS = """
QDialog#LoginDialog {
    background-color: #f4f6f8;
}
QLabel {
    color: #2c3e50;
}
QFrame#ShadowFrame {
    background-color: transparent;
    border: none;
}
QWidget#LoginCard {
    background-color: #ffffff;
    border: 1px solid #e1e5e8;
    border-radius: 12px;
}
QLineEdit#UsernameInput,
QLineEdit#PasswordInput {
    padding: 8px 10px;
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    background-color: #ffffff;
    color: #2c3e50;
    min-height: 40px;
}
QLineEdit#UsernameInput:focus,
QLineEdit#PasswordInput:focus {
    border: 2px solid #3498db;
}
QPushButton#EnterButton {
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
QPushButton#EnterButton:hover {
    background-color: #2980b9;
}
QPushButton#EnterButton:pressed {
    background-color: #1f618d;
}
QLabel#ErrorLabel {
    color: #c0392b;
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


class LoginDialog(QDialog):
    """Janela modal de login com decoração nativa e fundo opaco."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setFixedSize(480, 560)
        # Janela normal do sistema: sem FramelessWindowHint, sem
        # WA_TranslucentBackground (evita artefatos no Wayland).
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("LoginDialog")
        self.setStyleSheet(_QSS)

        # Layout raiz da janela (único).
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 28, 28, 28)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Frame vazio atrás do card, exclusivo para a sombra.
        # QGraphicsDropShadowEffect só neste frame, nunca no card.
        shadow_frame = QFrame(self)
        shadow_frame.setObjectName("ShadowFrame")
        shadow_frame.setContentsMargins(0, 0, 0, 0)

        shadow = QGraphicsDropShadowEffect(shadow_frame)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 4)
        shadow_frame.setGraphicsEffect(shadow)

        shadow_layout = QGridLayout(shadow_frame)
        shadow_layout.setContentsMargins(0, 0, 0, 0)

        # Card centralizado dentro do frame de sombra.
        card = QWidget(shadow_frame)
        card.setObjectName("LoginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # Logo.
        self._logo_label = QLabel(card)
        self._logo_label.setObjectName("LogoLabel")
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(72)
        card_layout.addWidget(self._logo_label)

        # Título.
        title = QLabel("NexoERP", card)
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        # Subtítulo.
        subtitle = QLabel("Sistema de Gestão Comercial", card)
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        # Campos.
        self._username = QLineEdit(card)
        self._username.setObjectName("UsernameInput")
        self._username.setPlaceholderText("Usuário")

        self._password = QLineEdit(card)
        self._password.setObjectName("PasswordInput")
        self._password.setPlaceholderText("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        # Formulário com rótulos.
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(14)
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)
        card_layout.addLayout(form)

        # Label de erro.
        self._error_label = QLabel(card)
        self._error_label.setObjectName("ErrorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()
        card_layout.addWidget(self._error_label)

        # Botão Entrar (default).
        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, card)
        self._buttons.setObjectName("EnterButtons")
        submit_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if submit_button is not None:
            submit_button.setObjectName("EnterButton")
            submit_button.setText("Entrar")
            submit_button.setDefault(True)

        self._buttons.accepted.connect(self._on_submit)
        card_layout.addWidget(self._buttons, alignment=Qt.AlignmentFlag.AlignCenter)

        shadow_layout.addWidget(card, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(shadow_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Carrega logo após o layout estar montado.
        self._load_logo()

    def _load_logo(self) -> None:
        """Carrega a logo em desenvolvimento ou no bundle PyInstaller."""
        path = resource_path("erp", "ui", "resources", "logo.png")
        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            logger.warning("Não foi possível carregar a logo do NexoERP: %s", path)
            self._logo_label.setText("NexoERP")
            return

        pixmap = pixmap.scaled(
            160,
            72,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._logo_label.setPixmap(pixmap)

    def set_presenter(self, presenter: LoginPresenter) -> None:
        self._presenter = presenter

    def show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def clear_password(self) -> None:
        self._password.clear()
        self._password.setFocus()

    def _on_submit(self) -> None:
        if self._presenter is None:
            logger.error("Tentativa de login sem LoginPresenter configurado.")
            self.show_error("O login não está disponível no momento.")
            return

        self._error_label.hide()
        self._presenter.login(
            self._username.text(),
            self._password.text(),
        )
