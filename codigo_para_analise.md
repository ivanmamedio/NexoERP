=== alembic.ini ===
[alembic]
# path to migration scripts
script_location = erp.shared.infrastructure.database:alembic

# version location
version_locations = erp.shared.infrastructure.database:alembic/versions

# sqlalchemy.url will be overridden programmatically at runtime
sqlalchemy.url = sqlite:///:memory:

# logging
[loggers]
keys = root,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

=== pyproject.toml ===
[project]
name = "erp"
version = "0.1.0"
description = "ERP desktop offline-first para pequenos comércios"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "AGPL-3.0-only" }
dependencies = [
    "alembic>=1.13",
    "bcrypt>=4.1",
    "platformdirs>=4.13.0",
    "PySide6>=6.7",
    "sqlalchemy>=2.1.4",
]

[dependency-groups]
dev = [
    "pytest>=8.2",
    "pytest-qt>=4.4",
    "ruff>=0.5",
    "mypy>=1.10",
    "import-linter>=2.0",
]
build = [
    "pyinstaller>=6.11",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/erp"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]

[tool.ruff.lint.isort]
known-first-party = ["erp"]

[tool.mypy]
strict = true
python_version = "3.12"
mypy_path = "src"
packages = ["erp"]

[[tool.mypy.overrides]]
module = ["PySide6.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
qt_api = "pyside6"
addopts = "-q"

=== .importlinter ===
[importlinter]
root_packages =
    erp

[importlinter:contract:modules-independent]
name = Modules must not import each other
type = independence
modules =
    erp.modules.audit
    erp.modules.backup
    erp.modules.cash
    erp.modules.catalog
    erp.modules.companies
    erp.modules.fiscal
    erp.modules.identity
    erp.modules.pricing
    erp.modules.receipts
    erp.modules.reports
    erp.modules.sales
    erp.modules.treasury

[importlinter:contract:shared-domain-purity]
name = Shared domain must not import application, infrastructure, or UI
type = forbidden
source_modules =
    erp.shared.domain
forbidden_modules =
    erp.shared.application
    erp.shared.infrastructure
    erp.shared.ui

=== src/erp/bootstrap.py ===
"""Composition root."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine

from erp.config import paths as app_paths
from erp.config.logging_config import setup_logging
from erp.shared.infrastructure.database.engine import build_engine
from erp.shared.infrastructure.database.migrations import run_migrations

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppContext:
    """Container for the services constructed at startup."""
    engine: Engine
    data_dir: Path
    db_path: Path


def bootstrap(*, data_dir: Path | None = None) -> AppContext:
    """Initialise logging, paths, database engine and run migrations."""
    resolved_data_dir = data_dir or app_paths.get_data_dir()
    resolved_data_dir.mkdir(parents=True, exist_ok=True)

    setup_logging()
    _logger.info("Starting ERP bootstrap (data_dir=%s)", resolved_data_dir)

    db_path = resolved_data_dir / "erp.db"
    engine = build_engine(db_path)

    # Migrations run synchronously at startup
    run_migrations(engine.url.render_as_string(hide_password=False))

    return AppContext(engine=engine, data_dir=resolved_data_dir, db_path=db_path)

=== src/erp/shared/infrastructure/database/__init__.py ===
"""Database infrastructure: engine, session factory, and declarative base."""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from erp.config.paths import get_data_dir
from erp.shared.infrastructure.database.engine import build_engine

class Base(DeclarativeBase):
    pass


def get_engine() -> Engine:
    """Create the default engine using the platform data directory."""
    data_dir = get_data_dir()
    db_path = data_dir / "erp.db"
    return build_engine(db_path)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


__all__ = ["Base", "build_engine", "get_engine", "get_session_factory"]

=== src/erp/shared/infrastructure/database/engine.py ===
"""SQLite engine factory with the PRAGMAs required by the project."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


def _apply_pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()


def build_engine(db_path: Path) -> Engine:
    """Create an engine for db_path and register the PRAGMA hook."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(url, future=True)
    event.listen(engine, "connect", _apply_pragmas)
    return engine


__all__ = ["build_engine"]

=== src/erp/shared/infrastructure/database/migrations.py ===
"""Programmatic Alembic runner."""
from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

_logger = logging.getLogger(__name__)
_ALEMBIC_DIR = Path(__file__).resolve().parent / "alembic"


def _build_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("logging.level.root", "WARNING")
    return cfg


def run_migrations(db_url: str, *, revision: str = "head") -> None:
    """Apply Alembic migrations up to revision (default head)."""
    cfg = _build_config(db_url)
    _logger.info("Running database migrations (target=%s)", revision)
    try:
        command.upgrade(cfg, revision)
    except Exception:
        _logger.exception("Database migration failed")
        raise

=== src/erp/shared/infrastructure/database/alembic/env.py ===
"""Alembic env.py — programmatic wiring."""
from __future__ import annotations

from logging.config import fileConfig  # noqa: F401 (kept for Alembic compat)

from alembic import context
from sqlalchemy import engine_from_config, pool

from erp.shared.infrastructure.database import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

=== src/erp/shared/infrastructure/database/alembic/versions/0001_initial.py ===
"""Create initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alembic_version",
        sa.Column("version_num", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("version_num"),
    )


def downgrade() -> None:
    op.drop_table("alembic_version")

=== src/erp/shared/infrastructure/database/alembic/versions/0002_identity_tables.py ===
"""Create identity tables

Revision ID: 0002_identity_tables
Revises: 0001_initial
Create Date: 2024-01-02 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_identity_tables"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_permissions_code"), "permissions", ["code"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "user_company_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )


def downgrade() -> None:
    op.drop_table("user_company_roles")
    op.drop_table("role_permissions")
    op.drop_table("users")
    op.drop_table("permissions")
    op.drop_table("roles")

=== src/erp/shared/infrastructure/database/alembic/versions/__init__.py ===

=== src/erp/modules/identity/domain/__init__.py ===
from .permission import Permission
from .role import Role
from .user import User

__all__ = ["Permission", "Role", "User"]


=== src/erp/modules/identity/domain/permission.py ===
"""Permission value object — código tipo 'product.price.update'."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    """Código de permissão do sistema.

    Exemplos: "product.price.update", "treasury.view", "cash.sangria",
    "sale.discount", "sale.cancel".
    """

    code: str

    def __post_init__(self) -> None:
        if not self.code or not isinstance(self.code, str):
            raise ValueError("Permission code must be a non-empty string")
        if " " in self.code:
            raise ValueError("Permission code must not contain spaces")


# Permissões do sistema (conforme QWEN.md e fases subsequentes)
PERMISSION_PRODUCT_PRICE_UPDATE = Permission("product.price.update")
PERMISSION_TREASURY_VIEW = Permission("treasury.view")
PERMISSION_CASH_SANGRIA = Permission("cash.sangria")
PERMISSION_SALE_DISCOUNT = Permission("sale.discount")
PERMISSION_SALE_CANCEL = Permission("sale.cancel")
PERMISSION_USER_MANAGE = Permission("user.manage")
PERMISSION_COMPANY_MANAGE = Permission("company.manage")
PERMISSION_CATALOG_MANAGE = Permission("catalog.manage")
PERMISSION_CASH_OPEN_CLOSE = Permission("cash.open_close")
PERMISSION_RECEIPT_PRINT = Permission("receipt.print")
PERMISSION_REPORTS_VIEW = Permission("reports.view")
PERMISSION_BACKUP_MANAGE = Permission("backup.manage")

ALL_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        PERMISSION_PRODUCT_PRICE_UPDATE,
        PERMISSION_TREASURY_VIEW,
        PERMISSION_CASH_SANGRIA,
        PERMISSION_SALE_DISCOUNT,
        PERMISSION_SALE_CANCEL,
        PERMISSION_USER_MANAGE,
        PERMISSION_COMPANY_MANAGE,
        PERMISSION_CATALOG_MANAGE,
        PERMISSION_CASH_OPEN_CLOSE,
        PERMISSION_RECEIPT_PRINT,
        PERMISSION_REPORTS_VIEW,
        PERMISSION_BACKUP_MANAGE,
    }
)

# Permissões por papel (seed)
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "Administrador": frozenset({p.code for p in ALL_PERMISSIONS}),
    "Gerente": frozenset(
        {
            "product.price.update",
            "treasury.view",
            "cash.sangria",
            "sale.discount",
            "sale.cancel",
            "user.manage",
            "company.manage",
            "catalog.manage",
            "cash.open_close",
            "receipt.print",
            "reports.view",
        }
    ),
    "Caixa": frozenset(
        {
            "sale.discount",
            "sale.cancel",
            "cash.open_close",
            "receipt.print",
        }
    ),
    "Financeiro": frozenset(
        {
            "treasury.view",
            "reports.view",
        }
    ),
}

=== src/erp/modules/identity/domain/role.py ===
"""Role entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Role(Entity):
    """Papel de usuário no sistema (ex.: Administrador, Caixa, Financeiro)."""

    id: int | None = field(default=None)
    name: str = field(default="")
    description: str = field(default="")
    is_active: bool = field(default=True)

=== src/erp/modules/identity/domain/user.py ===
"""User entity with password policy and lockout after 5 failed attempts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class User(Entity):
    """Usuário do sistema com controle de senha e bloqueio por tentativas falhas."""

    id: int | None = field(default=None)
    username: str = field(default="")
    password_hash: str = field(default="")
    must_change_password: bool = field(default=False)
    failed_login_attempts: int = field(default=0)
    locked_until: datetime | None = field(default=None)
    is_active: bool = field(default=True)
    company_id: int | None = field(default=None)

    def record_failed_login(self) -> None:
        """Incrementa tentativas falhas e bloqueia após 5."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    def reset_failed_logins(self) -> None:
        """Zera tentativas falhas após login bem-sucedido."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def is_locked(self) -> bool:
        """Retorna True se o usuário está bloqueado."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

=== src/erp/modules/identity/infrastructure/hasher.py ===
"""Bcrypt password hasher implementation."""

from __future__ import annotations

import bcrypt

from erp.modules.identity.application.ports import PasswordHasher


class BcryptHasher(PasswordHasher):
    """Password hasher using bcrypt."""

    def hash(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception:
            return False

=== src/erp/modules/identity/infrastructure/__init__.py ===
from erp.shared.infrastructure.database import Base

from .hasher import BcryptHasher
from .models import PermissionModel, RoleModel, UserModel
from .repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from .unit_of_work import SqlAlchemyIdentityUnitOfWork as _UoW  # noqa: F401

__all__ = [
    "Base",
    "BcryptHasher",
    "PermissionModel",
    "RoleModel",
    "SqlAlchemyIdentityUnitOfWork",
    "SqlAlchemyPermissionRepository",
    "SqlAlchemyRoleRepository",
    "SqlAlchemyUserRepository",
    "UserModel",
]

=== src/erp/modules/identity/infrastructure/models.py ===
"""SQLAlchemy models for identity module."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.shared.infrastructure.database import Base

# Tabela de associação many-to-many: role <-> permission
role_permission = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

# Tabela de associação many-to-many: user <-> role (com company_id)
user_company_role = Table(
    "user_company_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("company_id", Integer, nullable=True),
)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=user_company_role, back_populates="users"
    )


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    users: Mapped[list["UserModel"]] = relationship(
        secondary=user_company_role, back_populates="roles"
    )
    permissions: Mapped[list["PermissionModel"]] = relationship(
        secondary=role_permission, back_populates="roles"
    )


class PermissionModel(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=role_permission, back_populates="permissions"
    )

=== src/erp/modules/identity/infrastructure/repository.py ===
"""SQLAlchemy repositories for identity module."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.identity.application.ports import UserRepository
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.models import PermissionModel, RoleModel, UserModel, role_permission


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
        from sqlalchemy import insert, select

        role_model = self._session.execute(
            select(RoleModel).where(RoleModel.name == role_name)
        ).scalar_one_or_none()
        perm_model = self._session.execute(
            select(PermissionModel).where(PermissionModel.code == permission_code)
        ).scalar_one_or_none()

        if role_model is None or perm_model is None:
            return

        existing = self._session.execute(
            select(role_permission).where(
                role_permission.c.role_id == role_model.id,
                role_permission.c.permission_id == perm_model.id,
            )
        ).scalar_one_or_none()
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

=== src/erp/modules/identity/infrastructure/seed.py ===
"""Seed data for identity module: roles, permissions, and initial admin user."""

from __future__ import annotations

import os

from sqlalchemy.orm import Session

from erp.modules.identity.domain.permission import ALL_PERMISSIONS, ROLE_PERMISSIONS, Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)


def seed(*, session: Session, password_hasher: BcryptHasher) -> None:
    """Popula papéis e permissões do sistema.

    Não cria usuário administrador automaticamente. Use
    create_first_admin() para isso, fornecendo credenciais explícitas.
    """
    role_repo = SqlAlchemyRoleRepository(session)
    permission_repo = SqlAlchemyPermissionRepository(session)

    # 1. Criar permissões
    for perm in ALL_PERMISSIONS:
        existing = permission_repo.get_by_code(perm.code)
        if existing is None:
            permission_repo.add(perm)

    # 2. Criar papéis e associar permissões
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = role_repo.get_by_name(role_name)
        if role is None:
            role = Role(name=role_name, description=f"Papel {role_name}", is_active=True)
            role_repo.add(role)

        # Associar permissões ao papel (via tabela de associação role_permissions)
        for code in permission_codes:
            existing = permission_repo.get_by_code(code)
            if existing is None:
                new_perm = Permission(code=code)
                permission_repo.add(new_perm)
            role_repo.add_permission_to_role(role_name, code)

    session.commit()


def create_first_admin(
    *,
    session: Session,
    password_hasher: BcryptHasher,
    username: str,
    password: str,
) -> User | None:
    """Cria o primeiro usuário administrador, se ainda não existir.

    Não recria nem redefine a senha se o usuário já existe.
    Não grava senha em texto puro em nenhum log ou arquivo.
    """
    user_repo = SqlAlchemyUserRepository(session)

    existing = user_repo.get_by_username(username)
    if existing is not None:
        return None  # Não sobrescreve usuário existente

    admin_user = User(
        username=username,
        password_hash=password_hasher.hash(password),
        must_change_password=True,
        is_active=True,
    )
    user_repo.add(admin_user)
    session.commit()
    return admin_user


def get_admin_seed_password() -> str | None:
    """Lê a senha de seed do admin de variável de ambiente, se configurada.

    Não é usada automaticamente. Apenas disponível para scripts de
    inicialização que queiram definir a senha via variável de ambiente.
    Retorna None se não configurada.
    """
    return os.environ.get("NEXOERP_ADMIN_PASSWORD")

=== src/erp/modules/identity/infrastructure/unit_of_work.py ===
"""SQLAlchemy Unit of Work for identity module."""

from __future__ import annotations

from sqlalchemy.engine import Engine
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

    def __init__(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
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

=== tests/integration/test_bootstrap.py ===
"""Integration test: bootstrap creates the DB from scratch and honours PRAGMAs."""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text

from erp.bootstrap import bootstrap


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "erp_data"


def test_bootstrap_creates_db_with_required_pragmas(data_dir: Path) -> None:
    ctx = bootstrap(data_dir=data_dir)
    assert ctx.db_path.exists(), "Database file must be created by bootstrap"

    with ctx.engine.connect() as conn:
        journal_mode = conn.execute(text("PRAGMA journal_mode;")).scalar_one()
        foreign_keys = conn.execute(text("PRAGMA foreign_keys;")).scalar_one()
        busy_timeout = conn.execute(text("PRAGMA busy_timeout;")).scalar_one()

    assert journal_mode.lower() == "wal"
    assert int(foreign_keys) == 1
    assert int(busy_timeout) >= 5000


def test_bootstrap_is_idempotent(data_dir: Path) -> None:
    """Running bootstrap twice must not fail or corrupt the database."""
    first = bootstrap(data_dir=data_dir)
    second = bootstrap(data_dir=data_dir)
    assert first.db_path == second.db_path
    assert first.db_path.exists()

=== tests/integration/modules/identity/test_repository.py ===
"""Integration tests for identity repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.seed import create_first_admin, seed
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.infrastructure.database import Base


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_user_crud(session: Session) -> None:
    repo = SqlAlchemyUserRepository(session)

    user = User(
        username="joao",
        password_hash="hash123",
        must_change_password=True,
        is_active=True,
    )
    repo.add(user)

    saved = repo.get_by_username("joao")
    assert saved is not None
    assert saved.username == "joao"
    assert saved.must_change_password is True

    saved.password_hash = "novo_hash"
    repo.save(saved)

    updated = repo.get_by_username("joao")
    assert updated is not None
    assert updated.password_hash == "novo_hash"


def test_role_crud(session: Session) -> None:
    repo = SqlAlchemyRoleRepository(session)

    role = Role(name="Caixa", description="Papel de caixa", is_active=True)
    repo.add(role)

    saved = repo.get_by_name("Caixa")
    assert saved is not None
    assert saved.name == "Caixa"
    assert saved.is_active is True


def test_permission_crud(session: Session) -> None:
    repo = SqlAlchemyPermissionRepository(session)

    perm = Permission(code="product.price.update")
    repo.add(perm)

    saved = repo.get_by_code("product.price.update")
    assert saved is not None
    assert saved.code == "product.price.update"

    all_perms = repo.get_all()
    assert len(all_perms) == 1


def test_bcrypt_hasher_roundtrip() -> None:
    hasher = BcryptHasher()
    hashed = hasher.hash("senha123")
    assert hashed != "senha123"
    assert hasher.verify("senha123", hashed) is True
    assert hasher.verify("senha_errada", hashed) is False


def test_role_permission_persistence(session: Session) -> None:
    """Permissões de papel são persistidas na tabela role_permissions."""
    role_repo = SqlAlchemyRoleRepository(session)
    perm_repo = SqlAlchemyPermissionRepository(session)

    role = Role(name="Caixa", description="Papel de caixa", is_active=True)
    role_repo.add(role)

    perm = Permission(code="product.price.update")
    perm_repo.add(perm)

    role_repo.add_permission_to_role("Caixa", "product.price.update")
    session.commit()

    # Verificar que a associação existe (recuperar papel e verificar permissão)
    saved_role = role_repo.get_by_name("Caixa")
    assert saved_role is not None

    # A associação deve estar no banco (verificar via query direta)
    from erp.modules.identity.infrastructure.models import role_permission
    from sqlalchemy import select

    result = session.execute(
        select(role_permission).where(
            role_permission.c.role_id == saved_role.id,
        )
    ).scalars().all()
    assert len(result) == 1
    assert result[0].permission_id is not None


def test_seed_idempotent(session: Session) -> None:
    """Seed pode ser executado múltiplas vezes sem duplicar dados."""
    hasher = BcryptHasher()
    seed(session=session, password_hasher=hasher)
    seed(session=session, password_hasher=hasher)  # segunda vez

    perm_repo = SqlAlchemyPermissionRepository(session)
    perms = perm_repo.get_all()
    assert len(perms) == len({p.code for p in perms})  # sem duplicatas


def test_create_first_admin(session: Session) -> None:
    """Primeiro administrador é criado com credenciais explícitas."""
    hasher = BcryptHasher()

    # Primeira criação
    admin = create_first_admin(
        session=session,
        password_hasher=hasher,
        username="admin",
        password="senha_segura_123",
    )
    assert admin is not None
    assert admin.username == "admin"
    assert admin.must_change_password is True

    # Segunda tentativa com mesmo username não sobrescreve
    admin2 = create_first_admin(
        session=session,
        password_hasher=hasher,
        username="admin",
        password="outra_senha",
    )
    assert admin2 is None  # Não recria


def test_user_lockout_before_during_after(session: Session) -> None:
    """Bloqueio de login funciona antes, durante e depois do prazo."""
    user = User(
        username="teste",
        password_hash="hash123",
        must_change_password=False,
        is_active=True,
    )

    # Antes: não bloqueado
    assert user.is_locked() is False

    # Simular 5 tentativas falhas
    for _ in range(5):
        user.record_failed_login()

    # Durante: bloqueado (locked_until definido no futuro)
    assert user.failed_login_attempts == 5
    assert user.is_locked() is True
    assert user.locked_until is not None

    # Simular expiração do bloqueio (definir locked_until no passado)
    from datetime import datetime, timezone, timedelta
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert user.is_locked() is False  # Depois do prazo: desbloqueado

