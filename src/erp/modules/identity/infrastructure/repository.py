"""SQLAlchemy repositories for identity module."""

from __future__ import annotations

from typing import cast

from sqlalchemy import insert, select

from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.models import (
    PermissionModel,
    RoleModel,
    UserModel,
    role_permission,
    user_company_role,
)
from erp.shared.infrastructure.repository import SqlAlchemyRepository


class SqlAlchemyUserRepository(SqlAlchemyRepository[UserModel, User, int], UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    _model_cls = UserModel
    _company_id_column = "company_id"

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            password_hash=model.password_hash,
            must_change_password=model.must_change_password,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
            is_active=model.is_active,
            company_id=model.company_id,
            roles=[r.name for r in model.roles if r.is_active],
        )

    def _to_model(self, domain: User) -> UserModel:
        model = UserModel()
        model.username = domain.username
        model.password_hash = domain.password_hash
        model.must_change_password = domain.must_change_password
        model.failed_login_attempts = domain.failed_login_attempts
        model.locked_until = domain.locked_until
        model.is_active = domain.is_active
        model.company_id = domain.company_id
        return model

    def _copy_domain_to_model(self, domain: User, model: UserModel) -> None:
        """Override para pular o campo 'roles' (gerenciado via tabela de associação)."""
        for key in domain.__dataclass_fields__:
            if key in ("id", "roles"):  # id não atualiza, roles gerenciado via tabela associação
                continue
            value = getattr(domain, key)
            if hasattr(model, key):
                setattr(model, key, value)

    def list_all(self, *, company_id: int | None = None) -> list[User]:
        return cast(list[User], super().list_all(company_id=company_id))

    # ---- Custom queries beyond generic CRUD ----

    def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        stmt = self._apply_company_filter(stmt)
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def get_roles(self, user: User) -> list[Role]:
        if user.id is None:
            return []
        model = self._session.get(UserModel, user.id)
        if model is None:
            return []
        return [
            Role(
                id=r.id,
                name=r.name,
                description=r.description or "",
                is_active=r.is_active,
            )
            for r in model.roles
            if r.is_active
        ]

    def get_permissions(self, user: User) -> list[Permission]:
        if user.id is None:
            return []
        model = self._session.get(UserModel, user.id)
        if model is None:
            return []
        seen: set[str] = set()
        permissions: list[Permission] = []
        for role in model.roles:
            if not role.is_active:
                continue
            for perm in role.permissions:
                if perm.code in seen:
                    continue
                seen.add(perm.code)
                permissions.append(Permission(code=perm.code))
        return permissions

    def assign_role(self, user: User, role: Role, company_id: int | None = None) -> None:
        if user.id is None:
            raise ValueError("User must be persisted before assigning a role")
        if role.id is None:
            raise ValueError("Role must be persisted before assigning")

        # Idempotente: não duplica vínculo user-role já existente
        existing = self._session.execute(
            select(user_company_role).where(
                user_company_role.c.user_id == user.id,
                user_company_role.c.role_id == role.id,
            )
        ).first()
        if existing is not None:
            return

        self._session.execute(
            insert(user_company_role).values(
                user_id=user.id, role_id=role.id, company_id=company_id
            )
        )
        self._session.flush()


class SqlAlchemyRoleRepository(SqlAlchemyRepository[RoleModel, Role, int]):
    """SQLAlchemy repository for Role."""

    _model_cls = RoleModel
    _company_id_column = None  # Roles are global, not per-company

    def _to_domain(self, model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description or "",
            is_active=model.is_active,
        )

    def _to_model(self, domain: Role) -> RoleModel:
        model = RoleModel()
        model.name = domain.name
        model.description = domain.description
        model.is_active = domain.is_active
        return model

    # ---- Custom queries ----

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.name == name)
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def get_permissions(self, role: Role) -> list[Permission]:
        if role.id is None:
            return []
        model = self._session.get(RoleModel, role.id)
        if model is None:
            return []
        return [Permission(code=p.code) for p in model.permissions]

    def add_permission_to_role(self, role_name: str, permission_code: str) -> None:
        """Associa uma permissão a um papel na tabela role_permissions."""
        role_model = self._session.execute(
            select(RoleModel).where(RoleModel.name == role_name)
        ).scalar_one_or_none()
        perm_model = self._session.execute(
            select(PermissionModel).where(PermissionModel.code == permission_code)
        ).scalar_one_or_none()

        if role_model is None or perm_model is None:
            return

        existing = self._session.execute(
            select(role_permission.c.role_id).where(
                role_permission.c.role_id == role_model.id,
                role_permission.c.permission_id == perm_model.id,
            )
        ).first()
        if existing is not None:
            return

        self._session.execute(
            insert(role_permission).values(
                role_id=role_model.id,
                permission_id=perm_model.id,
            )
        )
        self._session.flush()


class SqlAlchemyPermissionRepository(SqlAlchemyRepository[PermissionModel, Permission, int]):
    """SQLAlchemy repository for Permission."""

    _model_cls = PermissionModel
    _company_id_column = None  # Permissions are global

    def _to_domain(self, model: PermissionModel) -> Permission:
        return Permission(code=model.code)

    def _to_model(self, domain: Permission) -> PermissionModel:
        model = PermissionModel()
        model.code = domain.code
        return model

    # ---- Custom queries ----

    def get_by_code(self, code: str) -> Permission | None:
        stmt = select(PermissionModel).where(PermissionModel.code == code)
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def get_all(self) -> list[Permission]:
        stmt = select(PermissionModel)
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]
