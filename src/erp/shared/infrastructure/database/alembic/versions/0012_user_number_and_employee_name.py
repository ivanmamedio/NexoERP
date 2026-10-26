"""Add user_number and employee_name to users, remove username.

Nova lógica de usuários:
- user_number: número sequencial único (0, 1, 2...) usado para login
- employee_name: nome do funcionário (exibição)
- username: REMOVIDO - substituído por user_number
- user_number 0 = admin obrigatório do sistema

FIX v0.1.1: Uses batch_alter_table for SQLite compatibility (no ALTER COLUMN SET NOT NULL)
"""

from __future__ import annotations

import contextlib

import sqlalchemy as sa
from alembic import op

revision: str = "0012_user_number_and_employee_name"
down_revision: str | None = "0011_backups"
branch_labels: str | None = None
depends_on: str | None = None

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

    # Check if username column exists
    columns = [col["name"] for col in inspector.get_columns("users")]
    has_username = "username" in columns

    # Check if index exists
    indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    has_username_index = "ix_users_username" in indexes

    _enable_bypass(connection)
    try:
        # 1. Drop index on username if it exists (must be before dropping column)
        if has_username_index:
            with op.batch_alter_table("users") as batch_op:
                batch_op.drop_index("ix_users_username")

        # 2. Adicionar colunas novas (nullable=True inicialmente)
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("user_number", sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column("employee_name", sa.String(200), nullable=True))

        # 3. Popular user_number sequencial baseado na ordem de criação (id)
        # Admin (id=1) fica com user_number = 0
        connection.execute(
            sa.text("UPDATE users SET user_number = id - 1")
        )

        # 4. Popular employee_name a partir do username existente (se existir)
        if has_username:
            connection.execute(
                sa.text("UPDATE users SET employee_name = username")
            )
        else:
            # Se não tem username, usar valor padrão
            connection.execute(
                sa.text("UPDATE users SET employee_name = 'Usuário ' || id")
            )

        # 5. Tornar user_number NOT NULL e UNIQUE (via batch_alter_table para SQLite)
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column("user_number", existing_type=sa.Integer(), nullable=False)
            batch_op.create_index("ix_users_user_number", ["user_number"], unique=True)

        # 6. Tornar employee_name NOT NULL
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column("employee_name", existing_type=sa.String(200), nullable=False)

        # 7. Remover coluna username (depois de migrar dados) - só se existir
        # SQLite tem limitações com DROP COLUMN, usamos batch_alter_table
        if has_username:
            with op.batch_alter_table("users") as batch_op:
                batch_op.drop_column("username")

        # 8. Atualizar sequence do user_number para próximos inserts
        # (SQLite não tem sequence, mas podemos usar trigger ou lógica na aplicação)
    finally:
        _disable_bypass(connection)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "users" not in inspector.get_table_names():
        return

    _enable_bypass(connection)
    try:
        # 1. Adicionar username de volta
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("username", sa.String(100), nullable=True))

        # 2. Popular username a partir de employee_name
        connection.execute(
            sa.text("UPDATE users SET username = employee_name")
        )

        # 3. Tornar username NOT NULL e UNIQUE
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column("username", existing_type=sa.String(100), nullable=False)
            batch_op.create_index("ix_users_username", ["username"], unique=True)

        # 4. Remover colunas novas
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_index("ix_users_user_number")
            batch_op.drop_column("user_number")
            batch_op.drop_column("employee_name")
    finally:
        _disable_bypass(connection)