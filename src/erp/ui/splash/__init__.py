"""Splash screen com logo do NexoERP."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen


class NexoERPSplashScreen(QSplashScreen):
    """Splash screen personalizada com logo do NexoERP."""

    def __init__(self, logo_path: Path | None = None) -> None:
        if logo_path is None:
            logo_path = Path(__file__).parent.parent / "resources" / "logo.png"

        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            # Fallback: cria pixmap simples se logo não carregar
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.white)

        # Escala mantendo proporção (max 500px largura)
        if pixmap.width() > 500:
            pixmap = pixmap.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)

        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setEnabled(False)

        # Centraliza na tela
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            self.move(
                (geometry.width() - self.width()) // 2,
                (geometry.height() - self.height()) // 2,
            )

    def show_message(
        self,
        message: str,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        color: Qt.GlobalColor = Qt.GlobalColor.black,
    ) -> None:
        """Mostra mensagem no splash."""
        self.showMessage(message, alignment, color)
        QApplication.processEvents()

    def finish_loading(self, main_window) -> None:
        """Finaliza splash e mostra janela principal."""
        self.finish(main_window)


def show_splash_screen(
    logo_path: Path | None = None, duration_ms: int = 1500
) -> NexoERPSplashScreen:
    """Cria e mostra splash screen por tempo determinado.

    Args:
        logo_path: Caminho opcional para logo customizada
        duration_ms: Tempo em ms para auto-fechar (0 = não auto-fechar)

    Returns:
        Instância do splash screen (caller deve chamar finish())
    """
    splash = NexoERPSplashScreen(logo_path)
    splash.show()
    QApplication.processEvents()

    if duration_ms > 0:
        QTimer.singleShot(duration_ms, splash.close)

    return splash
