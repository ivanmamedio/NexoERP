"""SQLAlchemy Unit of Work for identity module."""

from __future__ import annotations

from sqlalchemy.orm import Session

from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemyIdentityUnitOfWork(UnitOfWork):
    """Unit of Work implementation using SQLAlchemy session."""

    def __init__(self, engine) -> None:
        from sqlalchemy.engine import Engine
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self.users: SqlAlchemyUserRepository | None = None
        self.roles: SqlAlchemyRoleRepository | None = None
        self.permissions: SqlAlchemyPermissionRepository | None = None

    def __enter__(self) -> SqlAlchemyIdentityUnitOfWork:
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        self.roles = SqlAlchemyRoleRepository(self._session)
        self.permissions = SqlAlchemyPermissionRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        if self._session is not None:
            self._session.close()

    def commit(self) -> None:
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
