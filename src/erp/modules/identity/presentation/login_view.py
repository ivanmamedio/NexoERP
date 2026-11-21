"""Tela de login (Qt). Não contém regra de negócio — delega ao presenter."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
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


def _load_theme_qss() -> str:
    """Carrega o arquivo QSS do design system."""
    qss_path = Path(__file__).resolve().parent.parent.parent.parent / "shared" / "ui" / "theme.qss"
    try:
        return qss_path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - fallback silencioso
        logger.warning("Falha ao carregar stylesheet: %s", exc)
        return ""


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
        self.setStyleSheet(_load_theme_qss())

        # Widgets criados uma única vez.
        self._logo_label = QLabel()
        self._logo_label.setObjectName("LogoLabel")
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(72)

        self._title_label = QLabel("NexoERP")
        self._title_label.setObjectName("TitleLabel")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("font-size: 22px; font-weight: 600;")

        self._subtitle_label = QLabel("Sistema de Gestão Comercial")
        self._subtitle_label.setObjectName("SubtitleLabel")
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet("font-size: 12px; color: #6B7280;")

        self._user_number = QLineEdit()
        self._user_number.setPlaceholderText("Usuário (número ou nome)")
        self._user_number.setAccessibleName("Usuário (número ou nome)")

        self._password = QLineEdit()
        self._password.setPlaceholderText("Senha")
        self._password.setAccessibleName("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        self._error_label = QLabel()
        self._error_label.setObjectName("FormError")
        self._error_label.setWordWrap(True)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()

        self._submit_button = QPushButton("Entrar")
        self._submit_button.setObjectName("btnPrimary")
        self._submit_button.setDefault(True)
        self._submit_button.clicked.connect(self._on_submit)

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
        card.setObjectName("cardPrincipal")
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
        layout.addWidget(self._submit_button, alignment=center)
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
        identifier = self._user_number.text().strip()
        if not identifier:
            self.show_error("Informe o número ou nome do usuário.")
            return

        self._presenter.login(identifier, self._password.text())


def create_login_dialog(
    presenter: LoginPresenter | None = None,
    parent: QWidget | None = None,
) -> LoginDialog:
    dialog = LoginDialog(parent)
    if presenter is not None:
        dialog.set_presenter(presenter)
    return dialog
