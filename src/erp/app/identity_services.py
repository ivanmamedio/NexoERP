"""Implementação concreta de IdentityServices (composition root).

Cada método abre UM UnitOfWork — uma transação por caso de uso — e delega
para o caso de uso correspondente da camada application.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.identity.application.assign_role import (
    AssignRole,
    AssignRoleInput,
    AssignRoleOutput,
)
from erp.modules.identity.application.authenticate import (
    Authenticate,
    AuthenticateInput,
    AuthenticateOutput,
)
from erp.modules.identity.application.change_password import (
    ChangePassword,
    ChangePasswordInput,
    ChangePasswordOutput,
)
from erp.modules.identity.application.check_permission import (
    CheckPermission,
    CheckPermissionInput,
    CheckPermissionOutput,
)
from erp.modules.identity.application.create_user import (
    CreateUser,
    CreateUserInput,
    CreateUserOutput,
)
from erp.modules.identity.application.list_roles import (
    ListRoles,
    ListRolesInput,
    ListRolesOutput,
)
from erp.modules.identity.application.list_users import (
    ListUsers,
    ListUsersInput,
    ListUsersOutput,
)
from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import RoleRepository
from erp.modules.identity.application.reset_password_by_admin import (
    ResetPasswordByAdmin,
    ResetPasswordByAdminInput,
    ResetPasswordByAdminOutput,
)
from erp.modules.identity.application.set_user_active import (
    SetUserActive,
    SetUserActiveInput,
    SetUserActiveOutput,
)
from erp.modules.identity.domain.role import Role
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.unit_of_work import SqlAlchemyIdentityUnitOfWork


class SqlIdentityServices:
    """Fachada de identity sobre SQLAlchemy (1 transação por caso de uso)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._hasher = BcryptHasher()

    def authenticate(self, user_number: int, password: str) -> AuthenticateOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None
            result = Authenticate(uow.users, self._hasher).execute(
                AuthenticateInput(user_number=user_number, password=password)
            )
            uow.commit()
            return result

    def change_password(
        self,
        *,
        user_id: int,
        current_password: str | None,
        new_password: str,
        actor_id: int,
    ) -> ChangePasswordOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None
            result = ChangePassword(uow.users, self._hasher, PermissionGate(uow.users)).execute(
                ChangePasswordInput(
                    actor_id=actor_id,
                    user_id=user_id,
                    current_password=current_password,
                    new_password=new_password,
                )
            )
            uow.commit()
            return result

    def list_users(self, *, actor_id: int) -> ListUsersOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None
            result = ListUsers(uow.users, PermissionGate(uow.users)).execute(
                ListUsersInput(actor_id=actor_id)
            )
            uow.commit()
            return result

    def list_roles(self, *, actor_id: int) -> ListRolesOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.roles is not None and uow.users is not None
            result = ListRoles(uow.roles, PermissionGate(uow.users)).execute(
                ListRolesInput(actor_id=actor_id)
            )
            uow.commit()
            return result

    def create_user(
        self,
        *,
        employee_name: str,
        password: str,
        role_name: str,
        actor_id: int,
        must_change_password: bool = False,
    ) -> CreateUserOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None and uow.roles is not None
            role = self._require_role(uow.roles, role_name)
            result = CreateUser(uow.users, self._hasher, PermissionGate(uow.users)).execute(
                CreateUserInput(
                    actor_id=actor_id,
                    employee_name=employee_name,
                    password=password,
                    role_name=role_name,
                    must_change_password=must_change_password,
                ),
                role=role,
            )
            uow.commit()
            return result

    def assign_role(self, *, user_id: int, role_name: str, actor_id: int) -> AssignRoleOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None and uow.roles is not None
            result = AssignRole(uow.users, uow.roles, PermissionGate(uow.users)).execute(
                AssignRoleInput(actor_id=actor_id, user_id=user_id, role_name=role_name)
            )
            uow.commit()
            return result

    def set_user_active(
        self, *, user_id: int, is_active: bool, actor_id: int
    ) -> SetUserActiveOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None
            result = SetUserActive(uow.users, PermissionGate(uow.users)).execute(
                SetUserActiveInput(actor_id=actor_id, user_id=user_id, is_active=is_active)
            )
            uow.commit()
            return result

    def reset_password_by_admin(
        self,
        *,
        actor_id: int,
        target_user_id: int,
    ) -> ResetPasswordByAdminOutput:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None
            result = ResetPasswordByAdmin(uow.users, self._hasher, PermissionGate(uow.users)).execute(
                ResetPasswordByAdminInput(actor_id=actor_id, target_user_id=target_user_id)
            )
            uow.commit()
            return result

    def check_permission(self, *, user_id: int, permission_code: str) -> bool:
        with SqlAlchemyIdentityUnitOfWork(self._engine) as uow:
            assert uow.users is not None
            result: CheckPermissionOutput = CheckPermission(uow.users).execute(
                CheckPermissionInput(user_id=user_id, permission_code=permission_code)
            )
            uow.commit()
            return result.has_permission

    @staticmethod
    def _require_role(roles: RoleRepository, role_name: str) -> Role:
        role = roles.get_by_name(role_name)
        if role is None:
            raise ValueError(f"Papel '{role_name}' não encontrado")
        return role
