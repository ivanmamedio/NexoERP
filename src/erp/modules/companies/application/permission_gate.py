"""Permission gate for companies (company.manage)."""

from __future__ import annotations

from erp.modules.companies.application.ports import PermissionCheckerPort
from erp.modules.identity.domain.user import User
from erp.shared.domain.errors import PermissionDenied


class CompanyPermissionGate:
    """Verifies the company.manage permission for the current user.

    The gate is responsible for enforcing the rule at the use-case layer.
    """

    def __init__(self, permission_checker: PermissionCheckerPort) -> None:
        self._permission_checker = permission_checker

    def assert_can_manage_companies(self, actor_user: User) -> None:
        if not self._permission_checker.has_permission(actor_user, "company.manage"):
            raise PermissionDenied("Você não tem permissão para gerenciar empresas.")


