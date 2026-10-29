"""Unit tests for ListUsers case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.list_users import ListUsers, ListUsersInput
from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.shared.domain.errors import PermissionDenied


class FakeUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._users = users or []
        self._role_map: dict[int, list[Role]] = {}

    def add(self, user: User) -> None:
        self._users.append(user)

    def get_by_id(self, user_id: int) -> User | None:
        for u in self._users:
            if u.id == user_id:
                return u
        return None

    def get_by_user_number(self, user_number: int) -> User | None:
        for u in self._users:
            if u.user_number == user_number:
                return u
        return None

    def list_all(self, *, company_id: int | None = None) -> list[User]:
        return list(self._users)

    def get_roles(self, user: User) -> list[Role]:
        return self._role_map.get(user.id, [])

    def get_permissions(self, user: User) -> list[Permission]:
        return []

    def assign_role(self, user: User, role, company_id=None) -> None:
        pass

    def save(self, user: User) -> None:
        pass


class FakePermissionGate(PermissionGate):
    def __init__(self, allow: bool = True) -> None:
        super().__init__(FakeUserRepository())
        self.allow = allow

    def require(self, user_id: int, permission_code: str) -> None:
        if not self.allow:
            raise PermissionDenied(f"Permissão negada: '{permission_code}'.")


def _user(
    uid: int, user_number: int, employee_name: str, active: bool = True, must_change: bool = False
) -> User:
    return User(
        id=uid,
        user_number=user_number,
        employee_name=employee_name,
        is_active=active,
        must_change_password=must_change,
    )


def test_list_users_success() -> None:
    users = [
        _user(1, 0, "Ana", active=True),
        _user(2, 1, "Bruno", active=False),
        _user(3, 2, "Carla", active=True, must_change=True),
    ]
    repo = FakeUserRepository(users)
    gate = FakePermissionGate(allow=True)
    uc = ListUsers(repo, gate)

    output = uc.execute(ListUsersInput(actor_id=1))

    assert len(output.users) == 3
    assert output.users[0].employee_name == "Ana"
    assert output.users[0].user_number == 0
    assert output.users[0].is_active is True
    assert output.users[1].employee_name == "Bruno"
    assert output.users[1].user_number == 1
    assert output.users[1].is_active is False
    assert output.users[2].employee_name == "Carla"
    assert output.users[2].user_number == 2
    assert output.users[2].must_change_password is True


def test_list_users_requires_user_manage() -> None:
    repo = FakeUserRepository()
    gate = FakePermissionGate(allow=False)
    uc = ListUsers(repo, gate)

    with pytest.raises(PermissionDenied, match=r"user.manage"):
        uc.execute(ListUsersInput(actor_id=1))
