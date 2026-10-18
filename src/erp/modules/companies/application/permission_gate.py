"""Permission gate for companies (company.manage)."""

from __future__ import annotations

from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.user import User
from erp.shared.domain.errors import PermissionDenied


class CompanyPermissionGate:
    """Verifies the company.manage permission for the current user.

    The gate is responsible for enforcing the rule at the use-case layer.
    """

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def assert_can_manage_companies(self, actor_user: User) -> None:
        if not self._has_company_manage(actor_user):
            raise PermissionDenied("Você não tem permissão para gerenciar empresas.")

    def _has_company_manage(self, actor_user: User) -> bool:
        repository_user = self._users.get_by_id(actor_user.id or 0)
        if repository_user is None:
            return False
        return self._user_has_permission(repository_user, "company.manage")

    def _user_has_permission(self, user: User, code: str) -> bool:
        permissions = self._users.get_permissions(user)
        return any(p.code == code for p in permissions)


