"""Global exception handler for Qt application.

Provides centralized error handling with user-friendly dialogs,
logging, and error report copying capabilities.
"""

from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy.engine import Engine

_logger = logging.getLogger(__name__)


class GlobalExceptionHandler(QObject):
    """Global exception handler for the Qt application.

    Installs as the application's exception hook and provides
    a user-friendly error dialog with copy-to-clipboard functionality.
    """

    def __init__(self, app: QApplication, db_engine: Engine | None = None) -> None:
        super().__init__()
        self._app = app
        self._db_engine = db_engine
        self._original_excepthook = sys.excepthook

        # Install the handler
        sys.excepthook = self._handle_exception
        app.aboutToQuit.connect(self._on_about_to_quit)

    def _handle_exception(
        self,
        exc_type: type,
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        """Handle uncaught exceptions."""
        # Don't show dialog for KeyboardInterrupt or SystemExit
        if exc_type in (KeyboardInterrupt, SystemExit):
            self._original_excepthook(exc_type, exc_value, exc_tb)
            return

        # Format the full traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_text = "".join(tb_lines)

        # Log the full error
        _logger.critical("Uncaught exception:\n%s", tb_text)

        # Show error dialog (use QTimer to ensure it runs in the event loop)
        QTimer.singleShot(0, lambda: self._show_error_dialog(exc_type, exc_value, tb_text))

        # Call original hook for any other handlers
        self._original_excepthook(exc_type, exc_value, exc_tb)

    def _show_error_dialog(self, exc_type: type, exc_value: BaseException, tb_text: str) -> None:
        """Show user-friendly error dialog with copy option."""
        error_message = str(exc_value)

        # User-friendly message
        friendly_msg = (
            "Ocorreu um erro inesperado e o aplicativo precisa ser fechado.\n\n"
            f"Tipo do erro: {exc_type.__name__}\n"
            f"Mensagem: {error_message}\n\n"
            "Um relatório detalhado foi gerado. Você pode copiá-lo "
            "e enviar para a equipe de suporte."
        )

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Erro do Aplicativo")
        msg_box.setText(friendly_msg)

        # Add custom "Copiar Relatório" button
        copy_btn = msg_box.addButton("Copiar Relatório", QMessageBox.ButtonRole.ActionRole)
        close_btn = msg_box.addButton("Fechar", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(close_btn)

        # Store the full report for copying
        msg_box.setDetailedText(tb_text)

        # Add custom copy button behavior
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(tb_text))

        msg_box.exec()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        clipboard = self._app.clipboard()
        clipboard.setText(text)

        # Show brief confirmation
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Copiado")
        msg.setText("Relatório de erro copiado para a área de transferência.")
        ok_btn = msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msg.setDefaultButton(ok_btn)
        msg.exec()

    def _on_about_to_quit(self) -> None:
        """Clean up on application quit."""
        sys.excepthook = self._original_excepthook


def install_global_exception_handler(
    app: QApplication, db_engine: Engine | None = None
) -> GlobalExceptionHandler:
    """Install and return the global exception handler."""
    return GlobalExceptionHandler(app, db_engine)
