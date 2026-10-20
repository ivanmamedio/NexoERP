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
    QWidget,
)

if TYPE_CHECKING:
    from erp.modules.identity.presentation.login_presenter import LoginPresenter


class LoginDialog(QDialog):
    """Janela modal de login (usuário + senha) com logo de fundo."""

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setMinimumSize(420, 380)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Container principal com background
        self._container = QWidget(self)
        self._container.setObjectName("loginContainer")
        self._container.setStyleSheet("""
            #loginContainer {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)

        # Logo topo
        logo_path = Path(__file__).parent.parent.parent.parent / "ui" / "resources" / "logo.png"
        self._logo_label = QLabel(self._container)
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(180, Qt.TransformationMode.SmoothTransformation)
            self._logo_label.setPixmap(pixmap)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        self._title_label = QLabel("NexoERP", self._container)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet(
            "font-size: 24px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;"
        )

        # Subtítulo
        self._subtitle_label = QLabel("Sistema de Gestão Comercial", self._container)
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet(
            "font-size: 13px; color: #7f8c8d; margin-bottom: 24px;"
        )

        # Campos
        self._username = QLineEdit(self._container)
        self._username.setPlaceholderText("Usuário")
        self._username.setMinimumHeight(40)
        self._username.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)

        self._password = QLineEdit(self._container)
        self._password.setPlaceholderText("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setMinimumHeight(40)
        self._password.setStyleSheet(self._username.styleSheet())

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(16)
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)

        # Label de erro
        self._error_label = QLabel(self._container)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()

        # Botão
        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self._container)
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

        # Layout principal do container
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(40, 32, 40, 32)
        container_layout.setSpacing(16)
        container_layout.addWidget(self._logo_label)
        container_layout.addWidget(self._title_label)
        container_layout.addWidget(self._subtitle_label)
        container_layout.addLayout(form)
        container_layout.addWidget(self._error_label)
        container_layout.addWidget(self._buttons)

        # Layout do dialog (centraliza container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.addWidget(self._container, alignment=Qt.AlignmentFlag.AlignCenter)

        self._password.returnPressed.connect(self._on_submit)
        self._username.setFocus()

        # Sombra no container
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 4)
        self._container.setGraphicsEffect(shadow)

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