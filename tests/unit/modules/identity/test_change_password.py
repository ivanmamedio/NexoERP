"""Unit tests for ChangePassword case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.change_password import (
    ChangePassword,
    ChangePasswordInput,
)
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User


class FakeUserRepository(UserRepository):
    def __init__(self, user: User | None = None) -> None:
        self._user = user

    def add(self, user: User) -> None:
        pass

    def get_by_id(self, user_id: int) -> User | None:
        return self._user

    def get_by_username(self, username: str) -> User | None:
        return self._user

    def get_roles(self, user: User) -> list[Role]:
        return []

    def get_permissions(self, user: User) -> list[Permission]:
        return []

    def save(self, user: User) -> None:
        self._user = user


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hash({password})"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hash({password})"


def test_change_password_with_current_password() -> None:
    user = User(
        id=1,
        username="joao",
        password_hash="hash(senha_antiga)",
        is_active=True,
    )
    repo = FakeUserRepository(user)
    hasher = FakePasswordHasher()
    uc = ChangePassword(repo, hasher)

    result = uc.execute(
        ChangePasswordInput(
            user_id=1,
            current_password="senha_antiga",
            new_password="senha_nova",
        )
    )

    assert result.user_id == 1
    assert user.password_hash == "hash(senha_nova)"
    assert user.must_change_password is False


def test_change_password_without_current_password() -> None:
    """Quando current_password é None (primeiro acesso, must_change_password=True)."""
    user = User(
        id=1,
        username="joao",
        password_hash="hash(temp)",
        is_active=True,
        must_change_password=True,
    )
    repo = FakeUserRepository(user)
    hasher = FakePasswordHasher()
    uc = ChangePassword(repo, hasher)

    result = uc.execute(
        ChangePasswordInput(
            user_id=1,
            current_password=None,
            new_password="senha_nova",
        )
    )

    assert result.user_id == 1
    assert user.password_hash == "hash(senha_nova)"
    assert user.must_change_password is False


def test_change_password_wrong_current() -> None:
    user = User(
        id=1,
        username="joao",
        password_hash="hash(senha_antiga)",
        is_active=True,
    )
    repo = FakeUserRepository(user)
    hasher = FakePasswordHasher()
    uc = ChangePassword(repo, hasher)

    with pytest.raises(ValueError, match="Senha atual inválida"):
        uc.execute(
            ChangePasswordInput(
                user_id=1,
                current_password="senha_errada",
                new_password="senha_nova",
            )
        )


def test_change_password_user_not_found() -> None:
    repo = FakeUserRepository(None)
    hasher = FakePasswordHasher()
    uc = ChangePassword(repo, hasher)

    with pytest.raises(ValueError, match="Usuário não encontrado"):
        uc.execute(
            ChangePasswordInput(
                user_id=999,
                current_password="senha",
                new_password="nova",
            )
        )
