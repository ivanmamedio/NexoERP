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

    def get_by_username(self, username: str) -> User | None:
        for u in self._users:
            if u.username == username:
                return u
        return None

    def list_all(self) -> list[User]:
        return list(self._users)

    def get_roles(self, user: User) -> list[Role]:
        return self._role_map.get(user.id, [])

    def get_permissions(self, user: User) -> list[Permission]:
        return [Permission(code=p) for p in self._perms.get(user.username, [])]

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


def _user(uid: int, username: str, active: bool = True, must_change: bool = False) -> User:
    return User(
        id=uid,
        username=username,
        is_active=active,
        must_change_password=must_change,
    )


def test_list_users_success() -> None:
    users = [
        _user(1, "ana", active=True),
        _user(2, "bruno", active=False),
        _user(3, "carla", active=True, must_change=True),
    ]
    repo = FakeUserRepository(users)
    repo._perms = {"admin": ["user.manage"]}  # type: ignore[attr-defined]
    gate = FakePermissionGate(allow=True)
    uc = ListUsers(repo, gate)

    output = uc.execute(ListUsersInput(actor_id=1))

    assert len(output.users) == 3
    assert output.users[0].username == "ana"
    assert output.users[0].is_active is True
    assert output.users[1].username == "bruno"
    assert output.users[1].is_active is False
    assert output.users[2].username == "carla"
    assert output.users[2].must_change_password is True


def test_list_users_requires_user_manage() -> None:
    repo = FakeUserRepository()
    repo._perms = {"admin": []}  # type: ignore[attr-defined]
    gate = FakePermissionGate(allow=False)
    uc = ListUsers(repo, gate)

    with pytest.raises(PermissionDenied, match=r"user.manage"):
        uc.execute(ListUsersInput(actor_id=1))