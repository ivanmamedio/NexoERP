"""Unit tests for ListRoles case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.list_roles import ListRoles, ListRolesInput
from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import RoleRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.shared.domain.errors import PermissionDenied


class FakeRoleRepository(RoleRepository):
    def __init__(self, roles: list[Role] | None = None) -> None:
        self._roles = roles or []

    def get_by_name(self, name: str) -> Role | None:
        for r in self._roles:
            if r.name == name:
                return r
        return None

    def list_all(self) -> list[Role]:
        return list(self._roles)

    def get_permissions(self, role: Role) -> list[Permission]:
        return self._perm_map.get(role.id, [])


class FakeUserRepositoryForGate:
    def get_by_id(self, user_id: int):
        return None

    def get_permissions(self, user):
        return []


class FakePermissionGate(PermissionGate):
    def __init__(self, allow: bool = True) -> None:
        super().__init__(FakeUserRepositoryForGate())  # type: ignore[arg-type]
        self.allow = allow

    def require(self, user_id: int, permission_code: str) -> None:
        if not self.allow:
            raise PermissionDenied(f"Permissão negada: '{permission_code}'.")


def test_list_roles_success() -> None:
    admin_role = Role(id=1, name="Administrador", description="Admin", is_active=True)
    caixa_role = Role(id=2, name="Caixa", description="Caixa", is_active=True)
    repo = FakeRoleRepository([admin_role, caixa_role])
    repo._perm_map = {
        1: [Permission(code="user.manage"), Permission(code="company.manage")],
        2: [Permission(code="sale.discount")],
    }
    gate = FakePermissionGate(allow=True)
    uc = ListRoles(repo, gate)

    output = uc.execute(ListRolesInput(actor_id=1))

    assert len(output.roles) == 2
    assert output.roles[0].name == "Administrador"
    assert "user.manage" in output.roles[0].permission_codes
    assert output.roles[1].name == "Caixa"
    assert "sale.discount" in output.roles[1].permission_codes


def test_list_roles_requires_user_manage() -> None:
    repo = FakeRoleRepository()
    gate = FakePermissionGate(allow=False)
    uc = ListRoles(repo, gate)

    with pytest.raises(PermissionDenied, match=r"user.manage"):
        uc.execute(ListRolesInput(actor_id=1))
