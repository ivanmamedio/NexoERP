"""SQLAlchemy repositories for identity module."""

from __future__ import annotations

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

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


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        model = UserModel()
        model.username = user.username
        model.password_hash = user.password_hash
        model.must_change_password = user.must_change_password
        model.failed_login_attempts = user.failed_login_attempts
        model.locked_until = user.locked_until
        model.is_active = user.is_active
        model.company_id = user.company_id
        self._session.add(model)
        self._session.flush()
        user.id = model.id

    def get_by_id(self, user_id: int) -> User | None:
        model = self._session.get(UserModel, user_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

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

    def assign_role(
        self, user: User, role: Role, company_id: int | None = None
    ) -> None:
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

    def save(self, user: User) -> None:
        stmt = select(UserModel).where(UserModel.id == user.id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            self.add(user)
            return
        model.username = user.username
        model.password_hash = user.password_hash
        model.must_change_password = user.must_change_password
        model.failed_login_attempts = user.failed_login_attempts
        model.locked_until = user.locked_until
        model.is_active = user.is_active
        model.company_id = user.company_id

    def _model_to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            password_hash=model.password_hash,
            must_change_password=model.must_change_password,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
            is_active=model.is_active,
            company_id=model.company_id,
        )


class SqlAlchemyRoleRepository:
    """SQLAlchemy repository for Role."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.name == name)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return Role(
            id=model.id,
            name=model.name,
            description=model.description or "",
            is_active=model.is_active,
        )

    def add(self, role: Role) -> None:
        model = RoleModel()
        model.name = role.name
        model.description = role.description
        model.is_active = role.is_active
        self._session.add(model)
        self._session.flush()
        role.id = model.id

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


class SqlAlchemyPermissionRepository:
    """SQLAlchemy repository for Permission."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Permission | None:
        stmt = select(PermissionModel).where(PermissionModel.code == code)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return Permission(code=model.code)

    def get_all(self) -> list[Permission]:
        stmt = select(PermissionModel)
        models = self._session.execute(stmt).scalars().all()
        return [Permission(code=m.code) for m in models]

    def add(self, permission: Permission) -> None:
        model = PermissionModel()
        model.code = permission.code
        self._session.add(model)
        self._session.flush()
