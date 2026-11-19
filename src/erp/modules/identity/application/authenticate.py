"""Authenticate case of use.

Aceita login por número de usuário (sequencial) ou pelo nome do funcionário.
"""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.user import User


@dataclass(slots=True, frozen=True)
class AuthenticateInput:
    identifier: str  # número do usuário (ex: "0") ou nome do funcionário
    password: str


@dataclass(slots=True, frozen=True)
class AuthenticateOutput:
    user_id: int
    user_number: int
    employee_name: str
    company_id: int | None
    must_change_password: bool


class Authenticate:
    """Autentica um usuário verificando identificador e senha.

    O identificador pode ser o número sequencial do usuário
    ou o nome do funcionário (employee_name).
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(self, data: AuthenticateInput) -> AuthenticateOutput:
        user = self._resolve_user(data.identifier)
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
            user_number=user.user_number,
            employee_name=user.employee_name,
            company_id=user.company_id,
            must_change_password=user.must_change_password,
        )

    def _resolve_user(self, identifier: str) -> User | None:
        """Tenta resolver o identificador como número, depois como nome."""
        text = identifier.strip()
        if not text:
            return None

        # Se for puramente numérico, busca por user_number
        if text.isdigit():
            return self._user_repo.get_by_user_number(int(text))

        # Caso contrário, busca por employee_name
        return self._user_repo.get_by_employee_name(text)
