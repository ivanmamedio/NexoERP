"""Permission checker adapter for companies module.

Implements the PermissionCheckerPort using the identity module's UserRepository.
"""

from __future__ import annotations

from erp.modules.companies.application.ports import PermissionCheckerPort
from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.user import User


class SqlAlchemyPermissionChecker(PermissionCheckerPort):
    """Checks user permissions via the identity UserRepository."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def has_permission(self, user: User, permission_code: str) -> bool:
        if user.id is None:
            return False
        # Fetch fresh user from repository to get current permissions
        repo_user = self._user_repository.get_by_id(user.id)
        if repo_user is None:
            return False
        permissions = self._user_repository.get_permissions(repo_user)
        return any(p.code == permission_code for p in permissions)