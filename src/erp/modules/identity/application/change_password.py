"""ChangePassword case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.password_policy import validate_password_policy
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE


@dataclass(slots=True, frozen=True)
class ChangePasswordInput:
    actor_id: int
    user_id: int
    current_password: str | None
    new_password: str


@dataclass(slots=True, frozen=True)
class ChangePasswordOutput:
    user_id: int


class ChangePassword:
    """Altera a senha de um usuário.

    - Com ``current_password``: troca de senha self-service (verifica a senha
      atual).
    - Sem ``current_password``: ou é o próprio usuário (primeiro acesso /
      troca forçada), ou o actor precisa de ``user.manage`` (reset por admin).
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        gate: PermissionGate,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._gate = gate

    def execute(self, data: ChangePasswordInput) -> ChangePasswordOutput:
        user = self._user_repo.get_by_id(data.user_id)
        if user is None:
            raise ValueError("Usuário não encontrado")

        if data.current_password is not None:
            if not self._password_hasher.verify(
                data.current_password, user.password_hash
            ):
                raise ValueError("Senha atual inválida")
        elif data.actor_id != data.user_id:
            # Reset sem saber a senha atual só é permitido para administradores
            self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        validate_password_policy(data.new_password)
        user.password_hash = self._password_hasher.hash(data.new_password)
        user.must_change_password = False
        user.reset_failed_logins()
        self._user_repo.save(user)

        return ChangePasswordOutput(user_id=user.id or 0)
