"""Async password hasher using bcrypt in a background thread."""

from __future__ import annotations

from collections.abc import Callable

import bcrypt
from PySide6.QtCore import QObject, QThread, Signal


class _HashWorker(QObject):
    """Worker that performs bcrypt hashing in a background thread."""

    finished = Signal(str)  # hash result
    error = Signal(str)  # error message

    def __init__(self, password: str, cost: int = 12) -> None:
        super().__init__()
        self._password = password
        self._cost = cost

    def run(self) -> None:
        try:
            hashed = bcrypt.hashpw(self._password.encode("utf-8"), bcrypt.gensalt(self._cost))
            self.finished.emit(hashed.decode("utf-8"))
        except Exception as exc:
            self.error.emit(str(exc))


class _VerifyWorker(QObject):
    """Worker that verifies bcrypt hash in a background thread."""

    finished = Signal(bool)  # verification result
    error = Signal(str)  # error message

    def __init__(self, password: str, password_hash: str) -> None:
        super().__init__()
        self._password = password
        self._password_hash = password_hash

    def run(self) -> None:
        try:
            result = bcrypt.checkpw(
                self._password.encode("utf-8"), self._password_hash.encode("utf-8")
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class AsyncBcryptHasher:
    """Async bcrypt hasher that runs operations in background threads.

    Prevents UI freezing during password hashing/verification by offloading
    to QThread. Callbacks are invoked on the main thread via Qt's signal/slot.
    """

    def __init__(self, cost: int = 12) -> None:
        self._cost = cost

    def hash_async(
        self,
        password: str,
        on_success: Callable[[str], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """Hash password asynchronously.

        Args:
            password: Plain text password to hash.
            on_success: Callback receiving the hash string.
            on_error: Optional callback receiving error message.
        """
        thread = QThread()
        worker = _HashWorker(password, self._cost)
        worker.moveToThread(thread)

        def _on_finished(hash_str: str) -> None:
            on_success(hash_str)
            worker.deleteLater()
            thread.quit()

        def _on_error(error_msg: str) -> None:
            if on_error:
                on_error(error_msg)
            worker.deleteLater()
            thread.quit()

        thread.finished.connect(thread.deleteLater)
        thread.started.connect(worker.run)
        worker.finished.connect(_on_finished)
        worker.error.connect(_on_error)

        thread.start()

    def verify_async(
        self,
        password: str,
        password_hash: str,
        on_success: Callable[[bool], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """Verify password asynchronously.

        Args:
            password: Plain text password to verify.
            password_hash: Stored hash to verify against.
            on_success: Callback receiving True if match, False otherwise.
            on_error: Optional callback receiving error message.
        """
        thread = QThread()
        worker = _VerifyWorker(password, password_hash)
        worker.moveToThread(thread)

        def _on_finished(result: bool) -> None:
            on_success(result)
            worker.deleteLater()
            thread.quit()

        def _on_error(error_msg: str) -> None:
            if on_error:
                on_error(error_msg)
            worker.deleteLater()
            thread.quit()

        thread.finished.connect(thread.deleteLater)
        thread.started.connect(worker.run)
        worker.finished.connect(_on_finished)
        worker.error.connect(_on_error)

        thread.start()


# Convenience class for sync compatibility (uses default cost)
class SyncBcryptHasher:
    """Synchronous bcrypt hasher for cases where async is not needed."""

    def __init__(self, cost: int = 12) -> None:
        self._cost = cost

    def hash(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(self._cost))
        return hashed.decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False
