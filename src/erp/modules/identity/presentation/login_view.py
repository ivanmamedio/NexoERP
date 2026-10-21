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
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from erp.ui.resource_paths import resource_path

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """Janela modal de login com decoração nativa e fundo opaco."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._presenter = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setFixedSize(480, 560)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6f8;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(28, 28, 28, 28)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QWidget(self)
        self._card.setObjectName("loginCard")
        self._card.setStyleSheet("""
            QWidget#loginCard {
                background-color: #ffffff;
                border: 1px solid #e1e5e8;
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 4)
        self._card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # Logo placeholder (será preenchido em _load_logo)
        self._logo_label = QLabel(self._card)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(72)
        card_layout.addWidget(self._logo_label)

        # Título
        title = QLabel("NexoERP", self._card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #2c3e50; border: none;"
        )
        card_layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Sistema de Gestão Comercial", self._card)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 12px; color: #7f8c8d; border: none;"
        )
        card_layout.addWidget(subtitle)

        # Campos
        self._username = QLineEdit(self._card)
        self._username.setObjectName("usernameInput")
        self._username.setPlaceholderText("Usuário")
        self._username.setMinimumHeight(40)

        self._password = QLineEdit(self._card)
        self._password.setObjectName("passwordInput")
        self._password.setPlaceholderText("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setMinimumHeight(40)

        field_style = """
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """
        self._username.setStyleSheet(field_style)
        self._password.setStyleSheet(field_style)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(14)
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)
        card_layout.addLayout(form)

        self._error_label = QLabel(self._card)
        self._error_label.setWordWrap(True)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet(
            "color: #c0392b; font-size: 12px; border: none;"
        )
        self._error_label.hide()
        card_layout.addWidget(self._error_label)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok, self._card
        )
        submit_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if submit_button is not None:
            submit_button.setText("Entrar")
            submit_button.setMinimumHeight(40)
            submit_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 9px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 120px;
                }
                QPushButton:hover { background-color: #2980b9; }
                QPushButton:pressed { background-color: #1f618d; }
            """)

        self._buttons.accepted.connect(self._on_submit)
        card_layout.addWidget(
            self._buttons, alignment=Qt.AlignmentFlag.AlignCenter
        )

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(28, 28, 28, 28)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self._card)

        # Carrega logo APÓS o layout estar montado
        self._load_logo()

    def _load_logo(self) -> None:
        """Carrega a logo em desenvolvimento ou no bundle PyInstaller."""
        # Remove label antiga se existir
        if hasattr(self, '_logo_label') and self._logo_label is not None:
            # O label já está no layout, só atualiza o pixmap
            pass

        path = resource_path("erp", "ui", "resources", "logo.png")
        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            logger.warning("Não foi possível carregar a logo do NexoERP: %s", path)
            self._logo_label.setText("NexoERP")
            return

        # Cria/atualiza o pixmap
        pixmap = pixmap.scaled(
            160,
            72,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._logo_label.setPixmap(pixmap)

    def set_presenter(self, presenter) -> None:
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
