"""AssignRole case of use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.role import Role


@dataclass(slots=True, frozen=True)
class AssignRoleInput:
    user_id: int
    role_name: str
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class AssignRoleOutput:
    user_id: int
    role_name: str


class RoleRepository(Protocol):
    def get_by_name(self, name: str) -> Role | None: ...


class AssignRole:
    """Atribui um papel a um usuário."""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
    ) -> None:
        self._user_repo = user_repo
        self._role_repo = role_repo

    def execute(self, data: AssignRoleInput) -> AssignRoleOutput:
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
