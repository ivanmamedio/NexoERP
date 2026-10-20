"""Global exception handling for the ERP application."""

from __future__ import annotations

import logging
import traceback
from datetime import UTC, datetime
from types import TracebackType
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class ExceptionReporter(QObject):
    """Global exception reporter with logging and user notification."""

    exception_occurred = Signal(str, str)  # title, message

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("erp.exceptions")
        self._parent_widget: QWidget | None = None

    def set_parent_widget(self, widget: QWidget) -> None:
        """Set the parent widget for dialog display."""
        self._parent_widget = widget

    def handle_exception(
        self,
        exc: BaseException,
        context: str = "",
        show_dialog: bool = True,
    ) -> str:
        """Handle an exception globally.

        Args:
            exc: The exception to handle.
            context: Additional context about where the exception occurred.
            show_dialog: Whether to show a user-friendly dialog.

        Returns:
            The formatted error report string.
        """
        # Format the error report
        error_report = self._format_error_report(exc, context)

        # Log the error
        self._logger.error("Unhandled exception: %s", error_report)

        # Show user-friendly dialog if requested
        if show_dialog and self._parent_widget is not None:
            self._show_error_dialog(exc, context)

        # Emit signal for any other handlers
        self.exception_occurred.emit(
            type(exc).__name__,
            str(exc),
        )

        return error_report

    def _format_error_report(self, exc: BaseException, context: str) -> str:
        """Format a detailed error report."""
        lines = [
            "=" * 60,
            "ERRO DO SISTEMA - RELATÓRIO DE EXCEÇÃO",
            "=" * 60,
            f"Data/Hora: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Tipo: {type(exc).__name__}",
            f"Mensagem: {exc}",
            f"Contexto: {context}" if context else "Contexto: (não informado)",
            "",
            "TRACEBACK:",
            "-" * 60,
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            "=" * 60,
        ]
        return "\n".join(lines)

    def _show_error_dialog(self, exc: BaseException, context: str) -> None:
        """Show a user-friendly error dialog."""
        msg_box = QMessageBox(self._parent_widget)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Erro do Sistema")
        msg_box.setText(
            "Ocorreu um erro inesperado. A operação não pôde ser concluída."
        )

        # Create a detailed message
        detail = f"Tipo: {type(exc).__name__}\nMensagem: {exc}"
        if context:
            detail += f"\nContexto: {context}"

        msg_box.setDetailedText(detail)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

        # Add copy button functionality
        copy_btn = msg_box.addButton(
            "Copiar Relatório", QMessageBox.ButtonRole.ActionRole
        )
        if copy_btn:
            copy_btn.setText("Copiar Relatório")
            copy_btn.clicked.connect(lambda: self._copy_to_clipboard(detail))

        msg_box.exec()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(text)


# Global instance
_exception_reporter: ExceptionReporter | None = None


def get_exception_reporter() -> ExceptionReporter:
    """Get the global exception reporter instance."""
    global _exception_reporter
    if _exception_reporter is None:
        _exception_reporter = ExceptionReporter()
    return _exception_reporter


def install_global_exception_handler(parent_widget: QWidget | None = None) -> None:
    """Install global exception handlers for the application.

    Args:
        parent_widget: Optional parent widget for error dialogs.
    """
    import sys

    reporter = get_exception_reporter()
    if parent_widget:
        reporter.set_parent_widget(parent_widget)

    # Handle uncaught exceptions in the main thread
    def handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        reporter.handle_exception(
            exc_value,
            context="Exceção não tratada na thread principal",
            show_dialog=True,
        )

    sys.excepthook = handle_exception

    # Handle uncaught exceptions in Qt event loop
    from PySide6.QtCore import QCoreApplication

    def handle_qt_exception(exc: BaseException) -> None:
        reporter.handle_exception(
            exc,
            context="Exceção no loop de eventos Qt",
            show_dialog=True,
        )

    app = QCoreApplication.instance()
    if app is not None:
        app.aboutToQuit.connect(lambda: None)  # Keep reference
    # Note: Qt doesn't have a direct global exception handler for the event loop
    # Exceptions in event handlers must be caught locally or via try/except


def handle_exception_in_thread(
    exc: BaseException,
    thread_name: str = "",
    show_dialog: bool = False,
) -> str:
    """Handle an exception from a background thread.

    Args:
        exc: The exception to handle.
        thread_name: Name of the thread where the exception occurred.
        show_dialog: Whether to show a dialog (should be False for background threads).

    Returns:
        The formatted error report.
    """
    reporter = get_exception_reporter()
    context = f"Thread: {thread_name}" if thread_name else "Thread de fundo"
    return reporter.handle_exception(exc, context=context, show_dialog=show_dialog)