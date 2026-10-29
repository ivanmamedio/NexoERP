"""Unit tests for AssignRole case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.assign_role import AssignRole, AssignRoleInput
from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import RoleRepository, UserRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.shared.domain.errors import PermissionDenied


class FakeUserRepository(UserRepository):
    def __init__(self, user: User | None = None) -> None:
        self._user = user

    def add(self, user: User) -> None:
        pass

    def get_by_id(self, user_id: int) -> User | None:
        return self._user

    def get_by_user_number(self, user_number: int) -> User | None:
        return self._user

    def list_all(self, *, company_id: int | None = None) -> list[User]:
        return []

    def get_roles(self, user: User) -> list[Role]:
        return []

    def get_permissions(self, user: User) -> list[Permission]:
        if user is None:
            return []
        return [Permission(code=p) for p in self._perms.get(str(user.user_number), [])]

    def assign_role(self, user: User, role, company_id=None) -> None:
        pass

    def save(self, user: User) -> None:
        pass


class FakeRoleRepository(RoleRepository):
    def __init__(self, role: Role | None = None) -> None:
        self._role = role

    def get_by_name(self, name: str) -> Role | None:
        return self._role

    def list_all(self) -> list[Role]:
        return []

    def get_permissions(self, role: Role) -> list[Permission]:
        return []


class FakePermissionGate(PermissionGate):
    def __init__(self, allow: bool = True) -> None:
        super().__init__(FakeUserRepository())
        self.allow = allow

    def require(self, user_id: int, permission_code: str) -> None:
        if not self.allow:
            raise PermissionDenied(f"Permissão negada: '{permission_code}'.")


def test_assign_role_success() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    role = Role(id=2, name="Caixa", description="Caixa", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": ["user.manage"]}  # type: ignore[attr-defined]
    role_repo = FakeRoleRepository(role)
    gate = FakePermissionGate(allow=True)
    uc = AssignRole(repo, role_repo, gate)

    output = uc.execute(AssignRoleInput(actor_id=1, user_id=1, role_name="Caixa"))

    assert output.user_id == 1
    assert output.role_name == "Caixa"


def test_assign_role_user_not_found() -> None:
    repo = FakeUserRepository(None)
    role_repo = FakeRoleRepository()
    gate = FakePermissionGate(allow=True)
    uc = AssignRole(repo, role_repo, gate)

    with pytest.raises(ValueError, match="Usuário não encontrado"):
        uc.execute(AssignRoleInput(actor_id=1, user_id=999, role_name="Caixa"))


def test_assign_role_requires_user_manage() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    role = Role(id=2, name="Caixa", description="Caixa", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": []}  # type: ignore[attr-defined]
    role_repo = FakeRoleRepository(role)
    gate = FakePermissionGate(allow=False)
    uc = AssignRole(repo, role_repo, gate)

    with pytest.raises(PermissionDenied, match=r"user.manage"):
        uc.execute(AssignRoleInput(actor_id=1, user_id=1, role_name="Caixa"))
