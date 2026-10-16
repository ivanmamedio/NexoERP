"""SQLAlchemy repositories for identity module."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.models import PermissionModel, RoleModel, UserModel


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
        # Implementação simplificada - retorna vazio
        return []

    def get_permissions(self, user: User) -> list[Permission]:
        # Implementação simplificada - retorna vazio
        return []

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
            locked_until=model.locked_until.isoformat() if model.locked_until else None,
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
