"""Unit tests for CreateUser case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.create_user import (
    CreateUser,
    CreateUserInput,
)
from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.shared.domain.errors import PermissionDenied


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._next_id = 1
        self.assigned_roles: dict[int, Role] = {}

    def add(self, user: User) -> None:
        if user.username in self._users:
            raise ValueError(f"Usuário '{user.username}' já existe")
        user.id = self._next_id
        self._next_id += 1
        self._users[user.username] = user

    def get_by_id(self, user_id: int) -> User | None:
        for u in self._users.values():
            if u.id == user_id:
                return u
        return None

    def get_by_username(self, username: str) -> User | None:
        return self._users.get(username)

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def get_roles(self, user: User) -> list:
        return []

    def get_permissions(self, user: User) -> list:
        return []

    def assign_role(self, user: User, role, company_id=None) -> None:
        self.assigned_roles[user.id] = role

    def save(self, user: User) -> None:
        self._users[user.username] = user


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hash({password})"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hash({password})"


class FakePermissionGate(PermissionGate):
    """Simples double que aceita tudo, exceto quando configurado para negar."""

    def __init__(self) -> None:
        super().__init__(FakeUserRepository())
        self.deny = False

    def require(self, user_id: int, permission_code: str) -> None:
        if self.deny:
            from erp.shared.domain.errors import PermissionDenied

            raise PermissionDenied(f"Permissão negada: '{permission_code}'.")


def test_create_user_success() -> None:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    uc = CreateUser(repo, hasher, FakePermissionGate())

    role = Role(name="Caixa", description="Caixa", is_active=True)

    result = uc.execute(
        CreateUserInput(
            actor_id=1,
            username="joao",
            password="senha123",
            role_name="Caixa",
            must_change_password=False,
        ),
        role=role,
    )

    assert result.user_id == 1
    assert result.username == "joao"
    assert result.role_name == "Caixa"

    user = repo.get_by_username("joao")
    assert user is not None
    assert user.password_hash == "hash(senha123)"


def test_create_user_duplicate_username() -> None:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    uc = CreateUser(repo, hasher, FakePermissionGate())

    role = Role(name="Caixa", description="Caixa", is_active=True)

    uc.execute(
        CreateUserInput(
            actor_id=1,
            username="joao",
            password="senha123",
            role_name="Caixa",
        ),
        role=role,
    )

    with pytest.raises(ValueError, match="já existe"):
        uc.execute(
            CreateUserInput(
                actor_id=1,
                username="joao",
                password="senha456",
                role_name="Caixa",
            ),
            role=role,
        )


def test_create_user_requires_user_manage() -> None:
    """Sem user.manage, não se pode criar usuário."""
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    gate = FakePermissionGate()
    gate.deny = True
    uc = CreateUser(repo, hasher, gate)

    role = Role(name="Caixa", description="Caixa", is_active=True)

    with pytest.raises(PermissionDenied):
        uc.execute(
            CreateUserInput(
                actor_id=1,
                username="joao",
                password="senha123",
                role_name="Caixa",
            ),
            role=role,
        )
