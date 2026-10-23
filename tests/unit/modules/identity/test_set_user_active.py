"""Unit tests for SetUserActive case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.application.set_user_active import (
    SetUserActive,
    SetUserActiveInput,
)
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

    def get_permissions(self, user: User) -> list:
        return []

    def assign_role(self, user: User, role, company_id=None) -> None:
        pass

    def save(self, user: User) -> None:
        self._user = user


class FakePermissionGate(PermissionGate):
    def __init__(self, allow: bool = True) -> None:
        super().__init__(FakeUserRepository())
        self.allow = allow

    def require(self, user_id: int, permission_code: str) -> None:
        if not self.allow:
            raise PermissionDenied(f"Permissão negada: '{permission_code}'.")


def test_set_user_active_deactivate() -> None:
    user = User(id=2, user_number=1, employee_name="Maria", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"1": ["user.manage"]}  # type: ignore[attr-defined]
    gate = FakePermissionGate(allow=True)
    uc = SetUserActive(repo, gate)

    output = uc.execute(SetUserActiveInput(actor_id=1, user_id=2, is_active=False))

    assert output.user_id == 2
    assert output.is_active is False
    assert user.is_active is False


def test_set_user_active_cannot_deactivate_self() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": ["user.manage"]}  # type: ignore[attr-defined]
    gate = FakePermissionGate(allow=True)
    uc = SetUserActive(repo, gate)

    with pytest.raises(ValueError, match="não pode desativar o seu próprio"):
        uc.execute(SetUserActiveInput(actor_id=1, user_id=1, is_active=False))


def test_set_user_active_requires_user_manage() -> None:
    user = User(id=1, user_number=0, employee_name="João", is_active=True)
    repo = FakeUserRepository(user)
    repo._perms = {"0": []}  # type: ignore[attr-defined]
    gate = FakePermissionGate(allow=False)
    uc = SetUserActive(repo, gate)

    with pytest.raises(PermissionDenied, match=r"user.manage"):
        uc.execute(SetUserActiveInput(actor_id=1, user_id=1, is_active=False))


def test_set_user_active_user_not_found() -> None:
    repo = FakeUserRepository(None)
    gate = FakePermissionGate(allow=True)
    uc = SetUserActive(repo, gate)

    with pytest.raises(ValueError, match="Usuário não encontrado"):
        uc.execute(SetUserActiveInput(actor_id=1, user_id=999, is_active=False))
