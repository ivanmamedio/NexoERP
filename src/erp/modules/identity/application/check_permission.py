"""CheckPermission case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.user import User
from erp.modules.identity.application.ports import UserRepository


@dataclass(slots=True, frozen=True)
class CheckPermissionInput:
    user_id: int
    permission_code: str


@dataclass(slots=True, frozen=True)
class CheckPermissionOutput:
    user_id: int
    permission_code: str
    has_permission: bool


class CheckPermission:
    """Verifica se um usuário possui uma determinada permissão."""

    def __init__(
        self,
        user_repo: UserRepository,
    ) -> None:
        self._user_repo = user_repo

    def execute(self, data: CheckPermissionInput) -> CheckPermissionOutput:
        user = self._user_repo.get_by_id(data.user_id)
        if user is None:
            raise ValueError("Usuário não encontrado")

        permissions = self._user_repo.get_permissions(user)
        has_permission = any(
            p.code == data.permission_code for p in permissions
        )

        return CheckPermissionOutput(
            user_id=user.id or 0,
            permission_code=data.permission_code,
            has_permission=has_permission,
        )
