"""Unit tests for Authenticate case of use."""

from __future__ import annotations

import pytest

from erp.modules.identity.application.authenticate import (
    Authenticate,
    AuthenticateInput,
)
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.user import User


class FakeUserRepository(UserRepository):
    def __init__(self, user: User | None = None) -> None:
        self._user = user
        self.saved = False
        self.assigned_role = None

    def add(self, user: User) -> None:
        pass

    def get_by_id(self, user_id: int) -> User | None:
        return self._user

    def get_by_user_number(self, user_number: int) -> User | None:
        return self._user

    def get_roles(self, user: User) -> list:
        return []

    def get_permissions(self, user: User) -> list:
        return []

    def assign_role(self, user: User, role, company_id=None) -> None:
        self.assigned_role = role

    def save(self, user: User) -> None:
        self.saved = True


class FakePasswordHasher(PasswordHasher):
    def __init__(self, verify_result: bool = True) -> None:
        self._verify_result = verify_result

    def hash(self, password: str) -> str:
        return "hashed"

    def verify(self, password: str, password_hash: str) -> bool:
        return self._verify_result


def test_authenticate_success() -> None:
    user = User(
        id=1,
        user_number=0,
        employee_name="João",
        password_hash="hash",
        is_active=True,
    )
    repo = FakeUserRepository(user)
    hasher = FakePasswordHasher(verify_result=True)
    uc = Authenticate(repo, hasher)

    result = uc.execute(AuthenticateInput(user_number=0, password="senha123"))

    assert result.user_id == 1
    assert result.user_number == 0
    assert result.employee_name == "João"
    assert result.must_change_password is False


def test_authenticate_user_not_found() -> None:
    repo = FakeUserRepository(None)
    hasher = FakePasswordHasher()
    uc = Authenticate(repo, hasher)

    with pytest.raises(ValueError, match="Usuário ou senha inválidos"):
        uc.execute(AuthenticateInput(user_number=999, password="senha123"))


def test_authenticate_wrong_password() -> None:
    user = User(id=1, user_number=0, employee_name="João", password_hash="hash", is_active=True)
    repo = FakeUserRepository(user)
    hasher = FakePasswordHasher(verify_result=False)
    uc = Authenticate(repo, hasher)

    with pytest.raises(ValueError, match="Usuário ou senha inválidos"):
        uc.execute(AuthenticateInput(user_number=0, password="senha_errada"))

    assert user.failed_login_attempts == 1


def test_authenticate_inactive_user() -> None:
    user = User(id=1, user_number=0, employee_name="João", password_hash="hash", is_active=False)
    repo = FakeUserRepository(user)
    hasher = FakePasswordHasher(verify_result=True)
    uc = Authenticate(repo, hasher)

    with pytest.raises(ValueError, match="Usuário inativo"):
        uc.execute(AuthenticateInput(user_number=0, password="senha123"))
