"""Unit tests for CreateUser case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.create_user import (
    CreateUser,
    CreateUserInput,
)
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._next_id = 1

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

    def get_roles(self, user: User) -> list:
        return []

    def get_permissions(self, user: User) -> list:
        return []

    def save(self, user: User) -> None:
        self._users[user.username] = user


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hash({password})"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hash({password})"


def test_create_user_success() -> None:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    uc = CreateUser(repo, hasher)

    role = Role(name="Caixa", description="Caixa", is_active=True)

    result = uc.execute(
        CreateUserInput(
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
    uc = CreateUser(repo, hasher)

    role = Role(name="Caixa", description="Caixa", is_active=True)

    uc.execute(
        CreateUserInput(
            username="joao",
            password="senha123",
            role_name="Caixa",
        ),
        role=role,
    )

    with pytest.raises(ValueError, match="já existe"):
        uc.execute(
            CreateUserInput(
                username="joao",
                password="senha456",
                role_name="Caixa",
            ),
            role=role,
        )
