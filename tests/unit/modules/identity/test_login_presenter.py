"""Unit tests for LoginPresenter (sem janela Qt)."""

from __future__ import annotations

from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.presentation.login_presenter import LoginPresenter
from erp.shared.application.session import CurrentSession


class FakeIdentityServices(IdentityServices):
    def __init__(self) -> None:
        self.authenticate_calls = 0
        self.should_fail = False
        self.fail_message = "Usuário ou senha inválidos"
        self.must_change_password = False
        self.return_user_id = 1
        self.return_username = "joao"
        self.return_company_id = 1

    def authenticate(self, username: str, password: str):  # type: ignore[override]
        self.authenticate_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        from erp.modules.identity.application.authenticate import AuthenticateOutput

        return AuthenticateOutput(
            user_id=self.return_user_id,
            username=self.return_username,
            company_id=self.return_company_id,
            must_change_password=self.must_change_password,
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


def test_login_presenter_success() -> None:
    services = FakeIdentityServices()
    session = CurrentSession()
    view = FakeLoginView()
    presenter = LoginPresenter(view, services, session)

    result = presenter.login("joao", "senha123")

    assert result is True
    assert services.authenticate_calls == 1
    assert session.user_id == 1
    assert session.username == "joao"
    assert session.company_id == 1
    assert view.accepted is True
    assert view.errors == []


def test_login_presenter_propagates_company_id() -> None:
    """O login propaga o company_id para a CurrentSession."""
    services = FakeIdentityServices()
    services.return_company_id = 7
    session = CurrentSession()
    view = FakeLoginView()
    presenter = LoginPresenter(view, services, session)

    presenter.login("joao", "senha123")

    assert session.company_id == 7


def test_login_presenter_empty_fields() -> None:
    services = FakeIdentityServices()
    session = CurrentSession()
    view = FakeLoginView()
    presenter = LoginPresenter(view, services, session)

    result = presenter.login("", "senha123")

    assert result is False
    assert services.authenticate_calls == 0
    assert session.user_id is None
    assert view.errors == ["Informe usuário e senha."]


def test_login_presenter_invalid_credentials() -> None:
    services = FakeIdentityServices()
    services.should_fail = True
    session = CurrentSession()
    view = FakeLoginView()
    presenter = LoginPresenter(view, services, session)

    result = presenter.login("joao", "senha_errada")

    assert result is False
    assert session.user_id is None
    assert view.accepted is False
    assert view.errors == ["Usuário ou senha inválidos"]
    assert view.cleared_password is True


def test_login_presenter_sets_must_change_password() -> None:
    services = FakeIdentityServices()
    services.must_change_password = True
    session = CurrentSession()
    view = FakeLoginView()
    presenter = LoginPresenter(view, services, session)

    presenter.login("joao", "senha123")

    assert presenter.must_change_password is True


def test_login_presenter_logout() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, username="joao")
    view = FakeLoginView()
    presenter = LoginPresenter(view, services, session)

    presenter.logout()

    assert session.user_id is None
    assert session.username is None
    assert session.company_id is None
    assert presenter.must_change_password is False
