"""Fachada de serviços de identity usada pela apresentação.

Define o contrato (Protocol) que os presenters consomem. A implementação
concreta (com UnitOfWork) fica na camada de composição — ver
``erp.app.identity_services``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.identity.application.assign_role import AssignRoleOutput
from erp.modules.identity.application.authenticate import AuthenticateOutput
from erp.modules.identity.application.change_password import ChangePasswordOutput
from erp.modules.identity.application.create_user import CreateUserOutput
from erp.modules.identity.application.list_roles import ListRolesOutput
from erp.modules.identity.application.list_users import ListUsersOutput
from erp.modules.identity.application.set_user_active import SetUserActiveOutput


@runtime_checkable
class IdentityServices(Protocol):
    """Operações de identity expostas para a camada de apresentação."""

    def authenticate(self, username: str, password: str) -> AuthenticateOutput: ...

    def change_password(
        self,
        *,
        user_id: int,
        current_password: str | None,
        new_password: str,
        actor_id: int,
    ) -> ChangePasswordOutput: ...

    def list_users(self, *, actor_id: int) -> ListUsersOutput: ...

    def list_roles(self, *, actor_id: int) -> ListRolesOutput: ...

    def create_user(
        self,
        *,
        username: str,
        password: str,
        role_name: str,
        actor_id: int,
        must_change_password: bool = False,
    ) -> CreateUserOutput: ...

    def assign_role(self, *, user_id: int, role_name: str, actor_id: int) -> AssignRoleOutput: ...

    def set_user_active(
        self, *, user_id: int, is_active: bool, actor_id: int
    ) -> SetUserActiveOutput: ...

    def check_permission(self, *, user_id: int, permission_code: str) -> bool: ...
