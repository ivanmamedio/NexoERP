"""Tela de login (Qt). Não contém regra de negócio — delega ao presenter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from erp.modules.identity.presentation.login_presenter import LoginPresenter


class LoginDialog(QDialog):
    """Janela modal de login (usuário + senha) com logo no topo."""

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setFixedSize(400, 420)

        # Logo
        logo_path = Path(__file__).parent.parent.parent.parent / "ui" / "resources" / "logo.png"
        self._logo_label = QLabel(self)
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(160, Qt.TransformationMode.SmoothTransformation)
            self._logo_label.setPixmap(pixmap)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        self._title_label = QLabel("NexoERP", self)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #2c3e50; margin-bottom: 4px;"
        )

        # Subtítulo
        self._subtitle_label = QLabel("Sistema de Gestão Comercial", self)
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet(
            "font-size: 12px; color: #7f8c8d; margin-bottom: 20px;"
        )

        # Campos
        self._username = QLineEdit(self)
        self._username.setPlaceholderText("Usuário")
        self._username.setMinimumHeight(38)
        self._username.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)

        self._password = QLineEdit(self)
        self._password.setPlaceholderText("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setMinimumHeight(38)
        self._password.setStyleSheet(self._username.styleSheet())

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(14)
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)

        # Label de erro
        self._error_label = QLabel(self)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()

        # Botão
        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Entrar")
        self._buttons.accepted.connect(self._on_submit)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1a6fa0; }
        """)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)
        layout.addWidget(self._logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(form)
        layout.addWidget(self._error_label)
        layout.addWidget(self._buttons, alignment=Qt.AlignmentFlag.AlignCenter)

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