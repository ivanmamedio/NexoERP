"""Permission checker adapter for companies module.

Implements the PermissionCheckerPort using a user permission reader port.
"""

from __future__ import annotations

from erp.modules.companies.application.ports import (
    PermissionCheckerPort,
    UserPermissionReader,
)


class SqlAlchemyPermissionChecker(PermissionCheckerPort):
    """Checks user permissions via a UserPermissionReader port."""

    def __init__(self, permission_reader: UserPermissionReader) -> None:
        self._reader = permission_reader

    def has_permission(self, user_id: int, permission_code: str) -> bool:
        return permission_code in self._reader.get_permission_codes(user_id)
