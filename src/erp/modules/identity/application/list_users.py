"""ListUsers case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE


@dataclass(slots=True, frozen=True)
class ListUsersInput:
    actor_id: int


@dataclass(slots=True, frozen=True)
class UserListItem:
    user_id: int
    user_number: int
    employee_name: str
    is_active: bool
    must_change_password: bool
    is_locked: bool
    role_names: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ListUsersOutput:
    users: tuple[UserListItem, ...]


class ListUsers:
    """Lista todos os usuários (requer user.manage)."""

    def __init__(self, user_repo: UserRepository, gate: PermissionGate) -> None:
        self._user_repo = user_repo
        self._gate = gate

    def execute(self, data: ListUsersInput) -> ListUsersOutput:
        self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        items: list[UserListItem] = []
        for user in sorted(self._user_repo.list_all(), key=lambda u: u.user_number):
            roles = self._user_repo.get_roles(user)
            items.append(
                UserListItem(
                    user_id=user.id or 0,
                    user_number=user.user_number,
                    employee_name=user.employee_name,
                    is_active=user.is_active,
                    must_change_password=user.must_change_password,
                    is_locked=user.is_locked(),
                    role_names=tuple(r.name for r in roles),
                )
            )
        return ListUsersOutput(users=tuple(items))
