"""ResetPasswordByAdmin case of use — reset de senha por administrador."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE


@dataclass(slots=True, frozen=True)
class ResetPasswordByAdminInput:
    actor_id: int
    target_user_id: int


@dataclass(slots=True, frozen=True)
class ResetPasswordByAdminOutput:
    user_id: int
    user_number: int
    employee_name: str
    temporary_password: str  # sempre "novasenha"


class ResetPasswordByAdmin:
    """Permite que um admin resete a senha de outro usuário.

    A senha temporária é sempre "novasenha" e o usuário é forçado a trocar
    no próximo login (must_change_password = True).
    """

    TEMP_PASSWORD = "novasenha"

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        gate: PermissionGate,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._gate = gate

    def execute(self, data: ResetPasswordByAdminInput) -> ResetPasswordByAdminOutput:
        self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        if data.actor_id == data.target_user_id:
            raise ValueError(
                "Não é possível resetar a própria senha como admin. Use a troca de senha normal."
            )

        user = self._user_repo.get_by_id(data.target_user_id)
        if user is None:
            raise ValueError("Usuário não encontrado")

        # Define senha temporária "novasenha" e força troca no próximo login
        user.password_hash = self._password_hasher.hash(self.TEMP_PASSWORD)
        user.must_change_password = True
        user.reset_failed_logins()
        self._user_repo.save(user)

        return ResetPasswordByAdminOutput(
            user_id=user.id or 0,
            user_number=user.user_number,
            employee_name=user.employee_name,
            temporary_password=self.TEMP_PASSWORD,
        )
