"""Teste pytest-qt da tela de login (offscreen, sem exibir janela)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.presentation.login_presenter import LoginPresenter
from erp.modules.identity.presentation.login_view import LoginDialog
from erp.shared.application.session import CurrentSession


class FakeIdentityServices(IdentityServices):
    def __init__(self) -> None:
        self.calls = 0
        self.fail = False

    def authenticate(self, username: str, password: str):  # type: ignore[override]
        self.calls += 1
        if self.fail:
            raise ValueError("Usuário ou senha inválidos")
        from erp.modules.identity.application.authenticate import AuthenticateOutput

        return AuthenticateOutput(
            user_id=1, username="joao", company_id=1, must_change_password=False
        )

    def change_password(self, *, user_id, current_password, new_password, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def list_users(self, *, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def list_roles(self, *, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def create_user(self, *, username, password, role_name, actor_id, must_change_password=False):  # type: ignore[override]
        raise NotImplementedError

    def assign_role(self, *, user_id, role_name, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def set_user_active(self, *, user_id, is_active, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def check_permission(self, *, user_id, permission_code):  # type: ignore[override]
        raise NotImplementedError


def test_login_dialog_authenticates(qtbot):
    """O login com credenciais válidas autentica e fecha o diálogo."""
    services = FakeIdentityServices()
    session = CurrentSession()
    dialog = LoginDialog()
    presenter = LoginPresenter(dialog, services, session)
    dialog.set_presenter(presenter)

    qtbot.addWidget(dialog)
    dialog.show()

    dialog._username.setText("joao")
    dialog._password.setText("senha123")
    dialog._on_submit()

    assert services.calls == 1
    assert session.user_id == 1
    assert session.username == "joao"
    assert session.company_id == 1
    assert dialog.isVisible() is False  # accept() fecha o diálogo


def test_login_dialog_shows_error_on_invalid(qtbot):
    """Credenciais inválidas mostram erro e não fecham o diálogo."""
    services = FakeIdentityServices()
    services.fail = True
    session = CurrentSession()
    dialog = LoginDialog()
    presenter = LoginPresenter(dialog, services, session)
    dialog.set_presenter(presenter)

    qtbot.addWidget(dialog)
    dialog.show()

    dialog._username.setText("joao")
    dialog._password.setText("senha_errada")
    dialog._on_submit()

    assert services.calls == 1
    assert session.user_id is None
    assert dialog.isVisible() is True  # diálogo permanece aberto