"""Unit tests for UsersPresenter (sem janela Qt)."""

from __future__ import annotations

from erp.modules.identity.application.list_roles import RoleListItem
from erp.modules.identity.application.list_users import UserListItem
from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.presentation.users_presenter import UsersPresenter
from erp.shared.application.session import CurrentSession


class FakeIdentityServices(IdentityServices):
    def __init__(self) -> None:
        self.list_users_calls = 0
        self.list_roles_calls = 0
        self.create_calls = 0
        self.assign_calls = 0
        self.set_active_calls = 0
        self.should_fail = False
        self.fail_message = "Erro genérico"
        self.users_output = None
        self.roles_output = None

    def authenticate(self, user_number, password):  # type: ignore[override]
        raise NotImplementedError

    def change_password(self, *, user_id, current_password, new_password, actor_id):  # type: ignore[override]
        raise NotImplementedError

    def list_users(self, *, actor_id):  # type: ignore[override]
        self.list_users_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        from erp.modules.identity.application.list_users import ListUsersOutput

        return self.users_output or ListUsersOutput(users=())

    def list_roles(self, *, actor_id):  # type: ignore[override]
        self.list_roles_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        from erp.modules.identity.application.list_roles import ListRolesOutput

        return self.roles_output or ListRolesOutput(roles=())

    def create_user(self, *, employee_name, password, role_name, actor_id, must_change_password=False):  # type: ignore[override]
        self.create_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        from erp.modules.identity.application.create_user import CreateUserOutput

        return CreateUserOutput(
            user_id=1, user_number=0, employee_name=employee_name, role_name=role_name
        )

    def assign_role(self, *, user_id, role_name, actor_id):  # type: ignore[override]
        self.assign_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        from erp.modules.identity.application.assign_role import AssignRoleOutput

        return AssignRoleOutput(user_id=user_id, role_name=role_name)

    def set_user_active(self, *, user_id, is_active, actor_id):  # type: ignore[override]
        self.set_active_calls += 1
        if self.should_fail:
            raise ValueError(self.fail_message)
        from erp.modules.identity.application.set_user_active import SetUserActiveOutput

        return SetUserActiveOutput(user_id=user_id, is_active=is_active)

    def check_permission(self, *, user_id, permission_code):  # type: ignore[override]
        raise NotImplementedError

    def reset_password_by_admin(self, *, actor_id, target_user_id):  # type: ignore[override]
        raise NotImplementedError


class FakeUsersView:
    def __init__(self) -> None:
        self.rendered_users: list[UserListItem] = []
        self.rendered_roles: list[RoleListItem] = []
        self.errors: list[str] = []
        self.infos: list[str] = []
        self.cleared = False
        self.selected_id: int | None = None

    def render_users(self, users: list[UserListItem]) -> None:
        self.rendered_users = list(users)

    def render_roles(self, roles: list[RoleListItem]) -> None:
        self.rendered_roles = list(roles)

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def show_info(self, message: str) -> None:
        self.infos.append(message)

    def clear_user_form(self) -> None:
        self.cleared = True

    def selected_user_id(self) -> int | None:
        return self.selected_id


def test_users_presenter_load() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, user_number=0, username="admin")
    view = FakeUsersView()
    ListUsersOutput = __import__(
        "erp.modules.identity.application.list_users", fromlist=["ListUsersOutput"]
    ).ListUsersOutput
    ListRolesOutput = __import__(
        "erp.modules.identity.application.list_roles", fromlist=["ListRolesOutput"]
    ).ListRolesOutput
    services.users_output = ListUsersOutput(
        users=(
            UserListItem(
                user_id=1,
                user_number=0,
                employee_name="Ana",
                is_active=True,
                must_change_password=False,
                is_locked=False,
                role_names=("Caixa",),
            ),
        )
    )
    services.roles_output = ListRolesOutput(
        roles=(
            RoleListItem(name="Caixa", description="Caixa", permission_codes=("sale.discount",)),
        )
    )
    presenter = UsersPresenter(view, services, session)

    presenter.load()

    assert services.list_users_calls == 1
    assert services.list_roles_calls == 1
    assert len(view.rendered_users) == 1
    assert view.rendered_users[0].employee_name == "Ana"
    assert view.rendered_users[0].user_number == 0
    assert len(view.rendered_roles) == 1
    assert view.rendered_roles[0].name == "Caixa"


def test_users_presenter_create_user_success() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, user_number=0, username="admin")
    view = FakeUsersView()
    presenter = UsersPresenter(view, services, session)

    presenter.create_user("João", "senha1234", "Caixa")

    assert services.create_calls == 1
    assert view.cleared is True
    assert view.infos == ["Usuário 'João' criado com papel 'Caixa'."]
    assert services.list_users_calls == 1  # recarrega após criar


def test_users_presenter_create_user_validation() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, user_number=0, username="admin")
    view = FakeUsersView()
    presenter = UsersPresenter(view, services, session)

    presenter.create_user("", "senha1234", "Caixa")

    assert services.create_calls == 0
    assert view.errors == ["Informe o nome do funcionário."]


def test_users_presenter_create_user_requires_user_manage() -> None:
    services = FakeIdentityServices()
    services.should_fail = True
    services.fail_message = "Permissão negada: 'user.manage'."
    session = CurrentSession(user_id=1, user_number=0, username="admin")
    view = FakeUsersView()
    presenter = UsersPresenter(view, services, session)

    presenter.create_user("João", "senha1234", "Caixa")

    assert services.create_calls == 1
    assert view.errors == ["Permissão negada: 'user.manage'."]


def test_users_presenter_assign_role() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, user_number=0, username="admin")
    view = FakeUsersView()
    view.selected_id = 5
    presenter = UsersPresenter(view, services, session)

    presenter.assign_role("Gerente")

    assert services.assign_calls == 1
    assert view.infos == ["Papel 'Gerente' atribuído com sucesso."]
    assert services.list_users_calls == 1  # recarrega


def test_users_presenter_set_active() -> None:
    services = FakeIdentityServices()
    session = CurrentSession(user_id=1, user_number=0, username="admin")
    view = FakeUsersView()
    view.selected_id = 3
    presenter = UsersPresenter(view, services, session)

    presenter.set_active(False)

    assert services.set_active_calls == 1
    assert view.infos == ["Usuário desativado com sucesso."]


def test_users_presenter_no_session() -> None:
    services = FakeIdentityServices()
    session = CurrentSession()
    view = FakeUsersView()
    presenter = UsersPresenter(view, services, session)

    presenter.load()

    assert view.errors == ["Sessão expirada. Entre novamente."]
    assert services.list_users_calls == 0