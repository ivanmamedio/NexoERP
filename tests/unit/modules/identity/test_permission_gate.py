"""Unit tests for PermissionGate."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import Permission
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

    def get_roles(self, user: User) -> list:
        return []

    def get_permissions(self, user: User) -> list[Permission]:
        if user is None:
            return []
        return [Permission(code=p) for p in self._perms.get(str(user.user_number), [])]

    def assign_role(self, user: User, role, company_id=None) -> None:
        pass

    def save(self, user: User) -> None:
        pass


def test_gate_has_permission_true() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": ["user.manage", "company.manage"]}  # type: ignore[attr-defined]
    gate = PermissionGate(repo)

    assert gate.has(1, "user.manage") is True
    assert gate.has(1, "company.manage") is True
    assert gate.has(1, "catalog.manage") is False


def test_gate_has_permission_unknown_user() -> None:
    repo = FakeUserRepository(None)
    gate = PermissionGate(repo)

    assert gate.has(999, "user.manage") is False


def test_gate_require_granted() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": ["user.manage"]}  # type: ignore[attr-defined]
    gate = PermissionGate(repo)

    gate.require(1, "user.manage")  # não levanta


def test_gate_require_denied() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": []}  # type: ignore[attr-defined]
    gate = PermissionGate(repo)

    with pytest.raises(PermissionDenied, match="Permissão negada"):
        gate.require(1, "user.manage")