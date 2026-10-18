"""SetUserActive case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE


@dataclass(slots=True, frozen=True)
class SetUserActiveInput:
    actor_id: int
    user_id: int
    is_active: bool


@dataclass(slots=True, frozen=True)
class SetUserActiveOutput:
    user_id: int
    is_active: bool


class SetUserActive:
    """Ativa ou desativa um usuário (requer user.manage)."""

    def __init__(self, user_repo: UserRepository, gate: PermissionGate) -> None:
        self._user_repo = user_repo
        self._gate = gate

    def execute(self, data: SetUserActiveInput) -> SetUserActiveOutput:
        self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        user = self._user_repo.get_by_id(data.user_id)
        if user is None:
            raise ValueError("Usuário não encontrado")

        if user.id == data.actor_id and not data.is_active:
            raise ValueError("Você não pode desativar o seu próprio usuário.")

        user.is_active = data.is_active
        self._user_repo.save(user)

        return SetUserActiveOutput(user_id=user.id or 0, is_active=user.is_active)
