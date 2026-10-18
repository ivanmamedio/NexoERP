"""ListRoles case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import RoleRepository
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE


@dataclass(slots=True, frozen=True)
class ListRolesInput:
    actor_id: int


@dataclass(slots=True, frozen=True)
class RoleListItem:
    name: str
    description: str
    permission_codes: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ListRolesOutput:
    roles: tuple[RoleListItem, ...]


class ListRoles:
    """Lista os papéis do sistema com suas permissões (requer user.manage)."""

    def __init__(self, role_repo: RoleRepository, gate: PermissionGate) -> None:
        self._role_repo = role_repo
        self._gate = gate

    def execute(self, data: ListRolesInput) -> ListRolesOutput:
        self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        items: list[RoleListItem] = []
        for role in sorted(self._role_repo.list_all(), key=lambda r: r.name.lower()):
            codes = tuple(sorted(p.code for p in self._role_repo.get_permissions(role)))
            items.append(
                RoleListItem(
                    name=role.name,
                    description=role.description or "",
                    permission_codes=codes,
                )
            )
        return ListRolesOutput(roles=tuple(items))
