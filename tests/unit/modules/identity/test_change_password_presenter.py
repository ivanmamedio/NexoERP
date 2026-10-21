"""Unit tests for ChangePasswordPresenter (sem janela Qt)."""

from __future__ import annotations

from erp.modules.identity.application.change_password import ChangePasswordOutput
from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.presentation.change_password_presenter import ChangePasswordPresenter
from erp.shared.application.session import CurrentSession


class FakeIdentityServices(IdentityServices):
    def __init__(self) -> None:
        self.change_calls = 0
        self.should_fail = False
        self.fail_message = "Senha atual inválida"

    def authenticate(self, username, password):  # type: ignore[override]
        raise NotImplementedError

    def change_password(self, *, user_id, current_password, new_password, actor_id):  # type: ignore[override]
        self.change_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        return ChangePasswordOutput(user_id=user_id)

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


class FakeChangePasswordView:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.infos: list[str] = []
        self.cleared = False
        self.require_current = True
        self.accepted = False

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def show_info(self, message: str) -> None:
        self.infos.append(message)

    def clear_passwords(self) -> None:
        self.cleared = True

    def set_require_current(self, required: bool) -> None:
        self.require_current = required

    def accept(self) -> None:
        self.accepted = True


def test_change_password_presenter_self_service_success() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, username="joao")
    view = FakeChangePasswordView()
    presenter = ChangePasswordPresenter(view, services, session, forced=False)

    result = presenter.change("senha_antiga1", "senha_nova1", "senha_nova1")

    assert result is True
    assert services.change_calls == 1
    assert view.accepted is True
    assert view.infos == ["Senha alterada com sucesso."]


def test_change_password_presenter_forced_mode_no_current() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, username="joao")
    view = FakeChangePasswordView()
    presenter = ChangePasswordPresenter(view, services, session, forced=True)

    assert view.require_current is False
    result = presenter.change("", "senha_nova1", "senha_nova1")

    assert result is True
    # current_password deve ser None (forçado)
    assert services.change_calls == 1


def test_change_password_presenter_passwords_dont_match() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, username="joao")
    view = FakeChangePasswordView()
    presenter = ChangePasswordPresenter(view, services, session, forced=False)

    result = presenter.change("senha_antiga1", "senha_nova1", "outra_senha")

    assert result is False
    assert services.change_calls == 0
    assert view.errors == ["A confirmação não confere com a nova senha."]
    assert view.cleared is True


def test_change_password_presenter_service_error() -> None:
    services = FakeIdentityServices()
    services.should_fail = True
    session = CurrentSession(user_id=1, username="joao")
    view = FakeChangePasswordView()
    presenter = ChangePasswordPresenter(view, services, session, forced=False)

    result = presenter.change("senha_errada", "senha_nova1", "senha_nova1")

    assert result is False
    assert view.errors == ["Senha atual inválida"]
    assert view.cleared is True


def test_change_password_presenter_no_session() -> None:
    services = FakeIdentityServices()
    session = CurrentSession()
    view = FakeChangePasswordView()
    presenter = ChangePasswordPresenter(view, services, session, forced=False)

    result = presenter.change("senha", "nova", "nova")

    assert result is False
    assert view.errors == ["Sessão expirada. Entre novamente."]
