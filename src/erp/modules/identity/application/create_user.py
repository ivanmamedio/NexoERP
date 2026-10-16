"""CreateUser case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.application.ports import PasswordHasher, UserRepository


@dataclass(slots=True, frozen=True)
class CreateUserInput:
    username: str
    password: str
    role_name: str
    company_id: int | None = None
    must_change_password: bool = False


@dataclass(slots=True, frozen=True)
class CreateUserOutput:
    user_id: int
    username: str
    role_name: str


class CreateUser:
    """Cria um novo usuário associado a um papel."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(
        self,
        data: CreateUserInput,
        role: Role,
    ) -> CreateUserOutput:
        if self._user_repo.get_by_username(data.username) is not None:
            raise ValueError(f"Usuário '{data.username}' já existe")

        password_hash = self._password_hasher.hash(data.password)

        user = User(
            username=data.username,
            password_hash=password_hash,
            must_change_password=data.must_change_password,
            company_id=data.company_id,
        )
        self._user_repo.add(user)
        self._user_repo.save(user)

        return CreateUserOutput(
            user_id=user.id or 0,
            username=user.username,
            role_name=role.name,
        )
