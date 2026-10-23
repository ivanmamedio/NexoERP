"""SQLAlchemy models for identity module."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.shared.infrastructure.database import Base, TimestampMixin
from erp.shared.infrastructure.database.types import UTCDateTime

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


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=user_company_role, back_populates="users"
    )


class RoleModel(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["UserModel"]] = relationship(
        secondary=user_company_role, back_populates="roles"
    )
    permissions: Mapped[list["PermissionModel"]] = relationship(
        secondary=role_permission, back_populates="roles"
    )


class PermissionModel(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=role_permission, back_populates="permissions"
    )
