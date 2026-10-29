"""Tela de login (Qt). Não contém regra de negócio — delega ao presenter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from erp.ui.resource_paths import resource_path

if TYPE_CHECKING:
    from erp.modules.identity.presentation.login_presenter import LoginPresenter

logger = logging.getLogger(__name__)

_LOGO_WIDTH = 160
_SHADOW_MARGIN = 24
_CARD_MIN_WIDTH = 380

# Estilo único por objectName (definido em um único lugar).
_QSS = """
QDialog#LoginDialog {
    background-color: #f2f4f7;
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
    border: 1px solid #e0e0e0;
    border-radius: 12px;
}
QLineEdit#UserNumberInput,
QLineEdit#PasswordInput {
    padding: 8px 12px;
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    font-size: 14px;
    background-color: #ffffff;
    color: #2c3e50;
    selection-background-color: #3498db;
    min-height: 40px;
}
QLineEdit#UserNumberInput:focus,
QLineEdit#PasswordInput:focus {
    border: 2px solid #3498db;
}
QPushButton#EnterButton {
    background-color: #3498db;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
    min-width: 120px;
    min-height: 40px;
}
QPushButton#EnterButton:hover {
    background-color: #2980b9;
}
QPushButton#EnterButton:pressed {
    background-color: #1a6fa0;
}
QLabel#ErrorLabel {
    color: #e74c3c;
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
QLabel#LogoLabel {
    min-height: 72px;
}
"""


class LoginDialog(QDialog):
    """Diálogo modal de login: janela normal, card centralizado com sombra."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setObjectName("LoginDialog")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(_QSS)

        # Widgets criados uma única vez.
        self._logo_label = QLabel()
        self._logo_label.setObjectName("LogoLabel")
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(72)

        self._title_label = QLabel("NexoERP")
        self._title_label.setObjectName("TitleLabel")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._subtitle_label = QLabel("Sistema de Gestão Comercial")
        self._subtitle_label.setObjectName("SubtitleLabel")
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._user_number = QLineEdit()
        self._user_number.setObjectName("UserNumberInput")
        self._user_number.setPlaceholderText("Número do usuário")
        self._user_number.setAccessibleName("Número do usuário")
        self._user_number.setValidator(QIntValidator(0, 999999, self))

        self._password = QLineEdit()
        self._password.setObjectName("PasswordInput")
        self._password.setPlaceholderText("Senha")
        self._password.setAccessibleName("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        self._error_label = QLabel()
        self._error_label.setObjectName("ErrorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._buttons.setObjectName("EnterButtons")
        submit_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if submit_button is not None:
            submit_button.setObjectName("EnterButton")
            submit_button.setText("Entrar")
            submit_button.setDefault(True)
        self._buttons.accepted.connect(self._on_submit)

        self._load_logo()

        # Card (contém os campos) e host da sombra (frame VAZIO) são irmãos,
        # ocupando a mesma célula do grid: a sombra fica atrás do card sem tocar
        # nos filhos, evitando artefatos no Wayland.
        card = self._build_card()
        shadow_host = self._build_shadow_host()

        layout = QGridLayout(self)
        layout.setContentsMargins(_SHADOW_MARGIN, _SHADOW_MARGIN, _SHADOW_MARGIN, _SHADOW_MARGIN)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(shadow_host, 0, 0)
        layout.addWidget(card, 0, 0)
        card.raise_()

    # --- construção ---------------------------------------------------------

    def _build_shadow_host(self) -> QFrame:
        """Frame vazio (sem filhos) que carrega a sombra, evitando artefatos."""
        host = QFrame(self)
        host.setObjectName("ShadowFrame")
        effect = QGraphicsDropShadowEffect(host)
        effect.setBlurRadius(24)
        effect.setOffset(0, 4)
        effect.setColor(QColor(0, 0, 0, 70))
        host.setGraphicsEffect(effect)
        return host

    def _build_card(self) -> QFrame:
        card = QFrame(self)
        card.setObjectName("LoginCard")
        card.setMinimumWidth(_CARD_MIN_WIDTH)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)
        center = Qt.AlignmentFlag.AlignCenter
        layout.addWidget(self._logo_label, alignment=center)
        layout.addWidget(self._title_label, alignment=center)
        layout.addWidget(self._subtitle_label, alignment=center)
        layout.addWidget(self._user_number)
        layout.addWidget(self._password)
        layout.addWidget(self._error_label)
        layout.addWidget(self._buttons, alignment=center)
        return card

    def _load_logo(self) -> None:
        """Carrega a logo (dev e PyInstaller). Se faltar, esconde o rótulo sem quebrar."""
        path = resource_path("erp", "ui", "resources", "logo.png")
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logger.warning("Logo não encontrada ou inválida: %s", path)
            self._logo_label.hide()
            return
        ratio = self.devicePixelRatioF()
        scaled = pixmap.scaledToWidth(
            int(_LOGO_WIDTH * ratio), Qt.TransformationMode.SmoothTransformation
        )
        scaled.setDevicePixelRatio(ratio)
        self._logo_label.setPixmap(scaled)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # --- LoginView protocol -------------------------------------------------

    def set_presenter(self, presenter: LoginPresenter) -> None:
        self._presenter = presenter

    def show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def clear_password(self) -> None:
        self._password.clear()
        self._password.setFocus()

    # --- internals ----------------------------------------------------------

    def _on_submit(self) -> None:
        if self._presenter is None:
            logger.error("Tentativa de login sem LoginPresenter configurado.")
            self.show_error("O login não está disponível no momento.")
            return

        self._error_label.hide()
        user_number_text = self._user_number.text().strip()
        if not user_number_text:
            self.show_error("Informe o número do usuário.")
            return
        try:
            user_number = int(user_number_text)
        except ValueError:
            self.show_error("Número do usuário inválido.")
            return

        self._presenter.login(user_number, self._password.text())
