"""remove_username_column

Revision ID: 8706cf5235a7
Revises: 0012_user_number_and_employee_name
Create Date: 2026-10-23 20:14:51.030382
"""

from __future__ import annotations

import contextlib
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8706cf5235a7"
down_revision: str | None = "0012_user_number_and_employee_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BYPASS_ENABLE = "UPDATE audit_bypass SET enabled = 1 WHERE id = 1"
_BYPASS_DISABLE = "UPDATE audit_bypass SET enabled = 0 WHERE id = 1"


def _enable_bypass(connection: sa.engine.Connection) -> None:
    with contextlib.suppress(Exception):
        connection.execute(sa.text(_BYPASS_ENABLE))


def _disable_bypass(connection: sa.engine.Connection) -> None:
    with contextlib.suppress(Exception):
        connection.execute(sa.text(_BYPASS_DISABLE))


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "users" not in inspector.get_table_names():
        return

    _enable_bypass(connection)
    try:
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        # Get existing columns except username
        columns = [col["name"] for col in inspector.get_columns("users")]
        if "username" not in columns:
            return  # Already removed

        # Create new table without username
        connection.execute(
            sa.text("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_number INTEGER NOT NULL UNIQUE,
                employee_name VARCHAR(200) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                must_change_password BOOLEAN NOT NULL DEFAULT 0,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until DATETIME,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                company_id INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        )

        # Copy data
        connection.execute(
            sa.text("""
            INSERT INTO users_new (
                id, user_number, employee_name, password_hash, must_change_password,
                failed_login_attempts, locked_until, is_active, company_id,
                created_at, updated_at
            )
            SELECT id, user_number, employee_name, password_hash, must_change_password,
                   failed_login_attempts, locked_until, is_active, company_id,
                   created_at, updated_at
            FROM users
        """)
        )

        # Drop old table and rename
        connection.execute(sa.text("DROP TABLE users"))
        connection.execute(sa.text("ALTER TABLE users_new RENAME TO users"))

        # Recreate indexes
        connection.execute(
            sa.text("CREATE UNIQUE INDEX ix_users_user_number ON users (user_number)")
        )
    finally:
        _disable_bypass(connection)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "users" not in inspector.get_table_names():
        return

    _enable_bypass(connection)
    try:
        # Recreate table with username
        connection.execute(
            sa.text("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                must_change_password BOOLEAN NOT NULL DEFAULT 0,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until DATETIME,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                company_id INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        )

        # Copy data (username from employee_name)
        connection.execute(
            sa.text("""
            INSERT INTO users_new (
                id, username, password_hash, must_change_password,
                failed_login_attempts, locked_until, is_active, company_id,
                created_at, updated_at
            )
            SELECT id, employee_name, password_hash, must_change_password,
                   failed_login_attempts, locked_until, is_active, company_id,
                   created_at, updated_at
            FROM users
        """)
        )

        # Drop old table and rename
        connection.execute(sa.text("DROP TABLE users"))
        connection.execute(sa.text("ALTER TABLE users_new RENAME TO users"))

        # Recreate index
        connection.execute(sa.text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
    finally:
        _disable_bypass(connection)
