"""AssignRole case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import RoleRepository, UserRepository
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE


@dataclass(slots=True, frozen=True)
class AssignRoleInput:
    actor_id: int
    user_id: int
    role_name: str
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class AssignRoleOutput:
    user_id: int
    role_name: str


class AssignRole:
    """Atribui um papel a um usuário (requer user.manage)."""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        gate: PermissionGate,
    ) -> None:
        self._user_repo = user_repo
        self._role_repo = role_repo
        self._gate = gate

    def execute(self, data: AssignRoleInput) -> AssignRoleOutput:
        self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        user = self._user_repo.get_by_id(data.user_id)
        if user is None:
            raise ValueError("Usuário não encontrado")

        role = self._role_repo.get_by_name(data.role_name)
        if role is None:
            raise ValueError(f"Papel '{data.role_name}' não encontrado")

        # Persiste o vínculo user-role (gravação real no repositório)
        self._user_repo.assign_role(
            user, role, company_id=data.company_id or user.company_id
        )
        self._user_repo.save(user)

        return AssignRoleOutput(
            user_id=user.id or 0,
            role_name=role.name,
        )
