"""Teste pytest-qt da tela de login (offscreen, sem exibir janela)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox

from erp.modules.identity.application.authenticate import AuthenticateOutput
from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.presentation.login_presenter import LoginPresenter
from erp.modules.identity.presentation.login_view import LoginDialog
from erp.shared.application.session import CurrentSession


class FakeIdentityServices(IdentityServices):
    def __init__(self) -> None:
        self.calls = 0
        self.fail = False
        self.last_user_number: int | None = None
        self.last_password: str | None = None

    def authenticate(self, user_number: int, password: str):  # type: ignore[override]
        self.calls += 1
        self.last_user_number = user_number
        self.last_password = password
        if self.fail:
            raise ValueError("Usuário ou senha inválidos")

        return AuthenticateOutput(
            user_id=1, user_number=0, employee_name="João", company_id=1, must_change_password=False
        )

    def change_password(self, *, user_id, current_password, new_password, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def list_users(self, *, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def list_roles(self, *, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def create_user(
        self, *, employee_name, password, role_name, actor_id, must_change_password=False
    ):  # type: ignore[override]
        raise NotImplementedError

    def assign_role(self, *, user_id, role_name, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def set_user_active(self, *, user_id, is_active, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def check_permission(self, *, user_id, permission_code):  # type: ignore[override]
        raise NotImplementedError

    def reset_password_by_admin(self, *, actor_id, target_user_id):  # type: ignore[override]
        raise NotImplementedError


class FakeLoginView:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.cleared_password = False
        self.accepted = False

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def clear_password(self) -> None:
        self.cleared_password = True

    def accept(self) -> None:
        self.accepted = True


def test_login_dialog_no_frameless_no_translucent(qtbot):
    """O diálogo é uma janela normal (sem borda invisível nem fundo translúcido)."""
    CurrentSession()
    dialog = LoginDialog()

    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint == 0
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False

    qtbot.addWidget(dialog)


def test_login_dialog_logo_loads(qtbot):
    """A logo carrega (pixmap não nulo)."""
    dialog = LoginDialog()
    qtbot.addWidget(dialog)

    assert not dialog._logo_label.pixmap().isNull()


def test_login_dialog_enter_button_calls_presenter(qtbot):
    """O botão Entrar chama presenter.login com usuário e senha."""
    services = FakeIdentityServices()
    session = CurrentSession()
    dialog = LoginDialog()
    presenter = LoginPresenter(dialog, services, session)
    dialog.set_presenter(presenter)

    qtbot.addWidget(dialog)
    dialog.show()

    dialog._user_number.setText("0")
    dialog._password.setText("senha123")

    submit_button = dialog._buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert submit_button is not None
    assert submit_button.isDefault()
    submit_button.click()

    assert services.calls == 1
    assert services.last_user_number == 0
    assert services.last_password == "senha123"
    assert session.user_id == 1
    assert session.company_id == 1
    assert dialog.isVisible() is False  # accept() fecha o diálogo
