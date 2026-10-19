"""SQLAlchemy Unit of Work for identity module."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.infrastructure.unit_of_work_base import SqlAlchemyUnitOfWorkBase


class SqlAlchemyIdentityUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """Unit of Work for identity module."""

    def __init__(self, engine: Engine) -> None:
        super().__init__(
            engine,
            repo_factories={
                "users": lambda s: SqlAlchemyUserRepository(s),
                "roles": lambda s: SqlAlchemyRoleRepository(s),
                "permissions": lambda s: SqlAlchemyPermissionRepository(s),
            },
        )

    # Type hints for IDE support
    users: SqlAlchemyUserRepository | None = None
    roles: SqlAlchemyRoleRepository | None = None
    permissions: SqlAlchemyPermissionRepository | None = None