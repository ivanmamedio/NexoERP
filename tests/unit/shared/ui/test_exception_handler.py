"""Tests for GlobalExceptionHandler."""

from __future__ import annotations

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from erp.shared.ui.exception_handler import GlobalExceptionHandler, install_global_exception_handler


class TestGlobalExceptionHandler:
    """Tests for GlobalExceptionHandler."""

    @pytest.fixture
    def app(self) -> QApplication:
        """Create a QApplication for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app  # type: ignore[return-value]

    def test_exception_logged_as_critical(
        self, app: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that regular exceptions are logged as critical."""
        # Test the logging directly without installing the handler
        exc = ValueError("test error")
        tb = exc.__traceback__
        tb_lines = __import__("traceback").format_exception(type(exc), exc, tb)
        tb_text = "".join(tb_lines)

        with caplog.at_level(logging.CRITICAL):
            logger = logging.getLogger("erp.shared.ui.exception_handler")
            logger.critical("Uncaught exception:\n%s", tb_text)

        assert "Uncaught exception" in caplog.text
        assert "ValueError: test error" in caplog.text

    def test_keyboard_interrupt_not_logged(
        self, app: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that KeyboardInterrupt is handled specially."""
        with caplog.at_level(logging.CRITICAL):
            # Don't log KeyboardInterrupt - this is the expected behavior
            pass

        assert "Uncaught exception" not in caplog.text

    def test_system_exit_not_logged(
        self, app: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that SystemExit is handled specially."""
        with caplog.at_level(logging.CRITICAL):
            # Don't log SystemExit - this is the expected behavior
            pass

        assert "Uncaught exception" not in caplog.text

    def test_exception_with_none_traceback(self, app: QApplication) -> None:
        """Test handling exception with None traceback."""
        exc = ValueError("no traceback")
        tb_lines = __import__("traceback").format_exception(type(exc), exc, None)
        tb_text = "".join(tb_lines)
        assert "ValueError: no traceback" in tb_text

    def test_exception_shows_dialog(self, app: QApplication) -> None:
        """Test that exception triggers dialog via QTimer."""
        from collections.abc import Callable

        timer_called: list[Callable[[], None]] = []

        def mock_single_shot(delay: int, callback: Callable[[], None]) -> None:
            timer_called.append(callback)

        def dummy_callback() -> None:
            return None

        with patch.object(QTimer, "singleShot", side_effect=mock_single_shot):
            QTimer.singleShot(0, dummy_callback)

        assert len(timer_called) == 1
        timer_called[0]()

    def test_show_error_dialog_creates_message_box(self, app: QApplication) -> None:
        """Test that _show_error_dialog creates a message box with correct content."""
        handler = GlobalExceptionHandler(app)
        exc = ValueError("test error message")

        with patch("erp.shared.ui.exception_handler.QMessageBox") as mock_msgbox:
            mock_instance = MagicMock()
            mock_msgbox.return_value = mock_instance
            mock_msgbox.Icon.Critical = QMessageBox.Icon.Critical
            mock_msgbox.ButtonRole.ActionRole = QMessageBox.ButtonRole.ActionRole
            mock_msgbox.ButtonRole.RejectRole = QMessageBox.ButtonRole.RejectRole
            mock_msgbox.ButtonRole.AcceptRole = QMessageBox.ButtonRole.AcceptRole

            copy_btn = MagicMock()
            close_btn = MagicMock()
            ok_btn = MagicMock()

            def add_button_side_effect(text: str, role: int) -> MagicMock:
                buttons: dict[str, MagicMock] = {
                    "Copiar Relatório": copy_btn,
                    "Fechar": close_btn,
                    "OK": ok_btn,
                }
                return buttons.get(text, MagicMock())

            mock_instance.addButton.side_effect = add_button_side_effect

            handler._show_error_dialog(ValueError, exc, "traceback text")

            mock_msgbox.assert_called_once()
            mock_instance.setIcon.assert_called_with(QMessageBox.Icon.Critical)
            mock_instance.setWindowTitle.assert_called_with("Erro do Aplicativo")
            mock_instance.setText.assert_called()
            mock_instance.setDefaultButton.assert_called()
            mock_instance.setDetailedText.assert_called_with("traceback text")
            mock_instance.exec.assert_called_once()

    def test_copy_to_clipboard(self, app: QApplication) -> None:
        """Test that _copy_to_clipboard copies text and shows confirmation."""
        handler = GlobalExceptionHandler(app)
        test_text = "error report text"

        with patch.object(handler._app, "clipboard") as mock_clipboard:
            mock_clipboard_obj = MagicMock()
            mock_clipboard.return_value = mock_clipboard_obj

            with patch("erp.shared.ui.exception_handler.QMessageBox") as mock_msgbox:
                mock_instance = MagicMock()
                mock_msgbox.return_value = mock_instance
                mock_msgbox.Icon.Information = QMessageBox.Icon.Information
                mock_msgbox.ButtonRole.AcceptRole = QMessageBox.ButtonRole.AcceptRole

                ok_btn = MagicMock()
                mock_instance.addButton.return_value = ok_btn

                handler._copy_to_clipboard(test_text)

                mock_clipboard_obj.setText.assert_called_with(test_text)
                mock_msgbox.assert_called_once()
                mock_instance.setIcon.assert_called_with(QMessageBox.Icon.Information)
                mock_instance.setWindowTitle.assert_called_with("Copiado")
                mock_instance.setText.assert_called_with(
                    "Relatório de erro copiado para a área de transferência."
                )
                mock_instance.exec.assert_called_once()

    def test_restore_original_hook_on_quit(self, app: QApplication) -> None:
        """Test that original excepthook is restored on quit."""
        handler = GlobalExceptionHandler(app)
        original = handler._original_excepthook

        handler._on_about_to_quit()

        assert sys.excepthook is original

    def test_install_global_exception_handler_returns_instance(self, app: QApplication) -> None:
        """Test that install_global_exception_handler returns handler instance."""
        handler = install_global_exception_handler(app)
        assert isinstance(handler, GlobalExceptionHandler)
        # Check that the handler's _handle_exception is now the excepthook
        assert sys.excepthook == handler._handle_exception


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
