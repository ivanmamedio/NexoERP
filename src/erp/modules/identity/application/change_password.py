"""ChangePassword case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.password_policy import validate_password_policy


@dataclass(slots=True, frozen=True)
class ChangePasswordInput:
    user_id: int
    current_password: str | None
    new_password: str


@dataclass(slots=True, frozen=True)
class ChangePasswordOutput:
    user_id: int


class ChangePassword:
    """Altera a senha de um usuário."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(self, data: ChangePasswordInput) -> ChangePasswordOutput:
        user = self._user_repo.get_by_id(data.user_id)
        if user is None:
            raise ValueError("Usuário não encontrado")

        if data.current_password is not None and not self._password_hasher.verify(
            data.current_password, user.password_hash
        ):
            raise ValueError("Senha atual inválida")

        validate_password_policy(data.new_password)
        user.password_hash = self._password_hasher.hash(data.new_password)
        user.must_change_password = False
        user.reset_failed_logins()
        self._user_repo.save(user)

        return ChangePasswordOutput(user_id=user.id or 0)
