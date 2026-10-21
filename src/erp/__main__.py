"""Entry point: python -m erp.

Fluxo de identidade:
  1. Bootstrap (banco, migrations, seed).
  2. Splash screen com logo.
  3. Tela de login (modal).
  4. Se must_change_password=True -> tela de troca de senha (forçada).
  4. MainWindow com menus filtrados por permissão e guarda de sessão ociosa.
  5. Ao expirar a sessão ociosa, volta para o login.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog
from sqlalchemy.engine import Engine

from erp.app.identity_services import SqlIdentityServices
from erp.bootstrap import bootstrap
from erp.config.settings import get_session_timeout_minutes
from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.application.session import CurrentSession
from erp.shared.ui.resources import resource_path
from erp.ui.splash import show_splash_screen

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

    from erp.app.main_window import MainWindow

_logger = logging.getLogger(__name__)


class _AppContextHolder:
    engine: Engine | None = None


class _App:
    """Orquestra janelas de login, troca de senha e janela principal."""

    def __init__(self, app: QApplication, services: IdentityServices) -> None:
        self._app = app
        self._services = services
        self._session = CurrentSession()
        self._main_window: MainWindow | None = None

    def run(self) -> int:
        while True:
            self._session = CurrentSession()
            if not self._has_any_user():
                first_use_done = self._show_first_use()
                if not first_use_done:
                    # Usuário cancelou o primeiro uso; não pode prosseguir sem admin.
                    return 0
                continue

            logged_in = self._show_login()
            if not logged_in:
                return 0

            if self._session.user_id is None:
                continue

            if self._session.username and self._must_change_password():
                changed = self._show_change_password(forced=True)
                if not changed:
                    continue

            self._open_main_window()
            while self._main_window is not None and self._main_window.isVisible():
                self._app.processEvents()
        # Unreachable, but needed for type checker
        return 0

    def _has_any_user(self) -> bool:
        """Verifica se já existe pelo menos um usuário cadastrado."""
        engine = _AppContextHolder.engine
        if engine is None:
            return False
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            user_repo = SqlAlchemyUserRepository(session)
            return len(user_repo.list_all()) > 0

    def _show_first_use(self) -> bool:
        """Mostra a tela de primeiro uso para criar o primeiro administrador."""
        from erp.modules.identity.presentation.first_use_presenter import (
            FirstUsePresenter,
        )
        from erp.modules.identity.presentation.first_use_view import FirstUseDialog

        engine = _AppContextHolder.engine
        if engine is None:
            return False
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            hasher = BcryptHasher()
            user_repo = SqlAlchemyUserRepository(session)
            role_repo = SqlAlchemyRoleRepository(session)
            dialog = FirstUseDialog()
            presenter = FirstUsePresenter(
                view=dialog,
                user_repo=user_repo,
                password_hasher=hasher,
                session=self._session,
                role_repository=role_repo,
            )
            dialog.set_presenter(presenter)
            result = dialog.exec()
            session.commit()
            return result == QDialog.DialogCode.Accepted

    def _show_login(self) -> bool:
        from erp.modules.identity.presentation.login_presenter import LoginPresenter
        from erp.modules.identity.presentation.login_view import LoginDialog

        dialog = LoginDialog()
        presenter = LoginPresenter(dialog, self._services, self._session)
        dialog.set_presenter(presenter)
        dialog.exec()
        return self._session.is_authenticated()

    def _must_change_password(self) -> bool:
        from erp.modules.identity.infrastructure.unit_of_work import (
            SqlAlchemyIdentityUnitOfWork,
        )

        engine = _AppContextHolder.engine
        if engine is None:
            return False
        with SqlAlchemyIdentityUnitOfWork(engine) as uow:
            assert uow.users is not None
            user = uow.users.get_by_id(self._session.user_id or 0)
            if user is None:
                return False
            return bool(user.must_change_password)

    def _show_change_password(self, *, forced: bool) -> bool:
        from erp.modules.identity.presentation.change_password_presenter import (
            ChangePasswordPresenter,
        )
        from erp.modules.identity.presentation.change_password_view import (
            ChangePasswordDialog,
        )

        dialog = ChangePasswordDialog()
        presenter = ChangePasswordPresenter(dialog, self._services, self._session, forced=forced)
        dialog.set_presenter(presenter)
        dialog.exec()
        return not self._session.username or not self._must_change_password()

    def _open_main_window(self) -> None:
        from erp.app.main_window import MainWindow

        engine = _AppContextHolder.engine
        if engine is None:
            return
        timeout_minutes = get_session_timeout_minutes()
        self._main_window = MainWindow(
            services=self._services,
            session=self._session,
            idle_timeout_seconds=timeout_minutes * 60,
        )
        self._main_window.change_password_requested.connect(self._on_change_password_requested)
        self._main_window.users_requested.connect(self._on_users_requested)
        self._main_window.session_expired.connect(self._on_session_expired)
        self._main_window.start_session_guard()
        self._main_window.show()

    def _on_change_password_requested(self) -> None:
        self._show_change_password(forced=False)

    def _on_users_requested(self) -> None:
        from PySide6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self._main_window)
        layout = QVBoxLayout(dialog)
        from erp.modules.identity.presentation.users_presenter import UsersPresenter
        from erp.modules.identity.presentation.users_view import UsersWidget

        widget = UsersWidget(dialog)
        layout.addWidget(widget)
        dialog.setWindowTitle("Gerenciar Usuários")
        dialog.resize(700, 500)
        presenter = UsersPresenter(widget, self._services, self._session)
        widget.set_presenter(presenter)
        presenter.load()
        dialog.exec()

    def _on_session_expired(self) -> None:
        _logger.info("Sessão expirada por ociosidade")
        if self._main_window is not None:
            self._main_window.close()
            self._main_window = None


def main() -> int:
    try:
        ctx = bootstrap()
        _AppContextHolder.engine = ctx.engine
        _logger.info("Bootstrap successful. DB path: %s", ctx.db_path)
    except Exception:
        _logger.exception("Bootstrap failed")
        return 1

    if "CODESPACES" in os.environ or not os.environ.get("DISPLAY"):
        _logger.info("Running in headless environment. Skipping UI launch.")
        _logger.info("Run 'uv run pytest' to validate the infrastructure.")
        return 0

    from PySide6 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    # Splash screen - usa helper de recursos
    logo_path = resource_path("ui", "resources", "logo.png")
    splash = show_splash_screen(logo_path, duration_ms=0)  # 0 = não auto-fechar
    splash.showMessage(
        "Carregando módulos...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.white,
    )

    services: IdentityServices = SqlIdentityServices(ctx.engine)
    runner = _App(app, services)

    # Fecha splash quando janela principal abrir
    def on_main_window_ready() -> None:
        if hasattr(runner, "_main_window") and runner._main_window:
            splash.finish(runner._main_window)

    # Timer para fechar splash após UI carregar
    QTimer.singleShot(2000, on_main_window_ready)

    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
