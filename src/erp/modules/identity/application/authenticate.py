"""Authenticate case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.ports import PasswordHasher, UserRepository


@dataclass(slots=True, frozen=True)
class AuthenticateInput:
    username: str
    password: str


@dataclass(slots=True, frozen=True)
class AuthenticateOutput:
    user_id: int
    username: str
    must_change_password: bool


class Authenticate:
    """Autentica um usuário verificando username e senha."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(self, data: AuthenticateInput) -> AuthenticateOutput:
        user = self._user_repo.get_by_username(data.username)
        if user is None:
            raise ValueError("Usuário ou senha inválidos")

        if user.is_locked():
            raise ValueError("Usuário bloqueado por tentativas falhas excessivas")

        if not user.is_active:
            raise ValueError("Usuário inativo")

        if not self._password_hasher.verify(data.password, user.password_hash):
            user.record_failed_login()
            self._user_repo.save(user)
            raise ValueError("Usuário ou senha inválidos")

        user.reset_failed_logins()
        self._user_repo.save(user)

        return AuthenticateOutput(
            user_id=user.id or 0,
            username=user.username,
            must_change_password=user.must_change_password,
        )
