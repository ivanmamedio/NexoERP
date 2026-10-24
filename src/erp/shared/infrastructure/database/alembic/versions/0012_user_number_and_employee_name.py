"""Add user_number and employee_name to users, remove username.

Nova lógica de usuários:
- user_number: número sequencial único (0, 1, 2...) usado para login
- employee_name: nome do funcionário (exibição)
- username: REMOVIDO - substituído por user_number
- user_number 0 = admin obrigatório do sistema
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0012_user_number_and_employee_name"
down_revision: str | None = "0011_backups"
branch_labels: str | None = None
depends_on: str | None = None

_BYPASS_ENABLE = "UPDATE audit_bypass SET enabled = 1 WHERE id = 1"
_BYPASS_DISABLE = "UPDATE audit_bypass SET enabled = 0 WHERE id = 1"


def _enable_bypass(connection: sa.engine.Connection) -> None:
    try:
        connection.execute(sa.text(_BYPASS_ENABLE))
    except Exception:
        pass


def _disable_bypass(connection: sa.engine.Connection) -> None:
    try:
        connection.execute(sa.text(_BYPASS_DISABLE))
    except Exception:
        pass


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "users" not in inspector.get_table_names():
        return

    # Check if username column exists
    columns = [col["name"] for col in inspector.get_columns("users")]
    has_username = "username" in columns

    _enable_bypass(connection)
    try:
        # 1. Adicionar colunas novas
        connection.execute(sa.text("""
            ALTER TABLE users ADD COLUMN user_number INTEGER
        """))
        connection.execute(sa.text("""
            ALTER TABLE users ADD COLUMN employee_name VARCHAR(200)
        """))

        # 2. Popular user_number sequencial baseado na ordem de criação (id)
        # Admin (id=1) fica com user_number = 0
        connection.execute(sa.text("""
            UPDATE users SET user_number = id - 1
        """))

        # 3. Popular employee_name a partir do username existente (se existir)
        if has_username:
            connection.execute(sa.text("""
                UPDATE users SET employee_name = username
            """))
        else:
            # Se não tem username, usar valor padrão
            connection.execute(sa.text("""
                UPDATE users SET employee_name = 'Usuário ' || id
            """))

        # 4. Tornar user_number NOT NULL e UNIQUE
        connection.execute(sa.text("""
            ALTER TABLE users ALTER COLUMN user_number SET NOT NULL
        """))
        connection.execute(sa.text("""
            CREATE UNIQUE INDEX ix_users_user_number ON users (user_number)
        """))

        # 5. Tornar employee_name NOT NULL
        connection.execute(sa.text("""
            ALTER TABLE users ALTER COLUMN employee_name SET NOT NULL
        """))

        # 6. Remover coluna username (depois de migrar dados) - só se existir
        # SQLite tem limitações com DROP COLUMN, então usamos try/except
        try:
            connection.execute(sa.text("""
                ALTER TABLE users DROP COLUMN username
            """))
        except Exception:
            # Ignorar se a coluna não existir ou não puder ser removida
            pass

        # 6. Atualizar sequence do user_number para próximos inserts
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
        connection.execute(sa.text("""
            ALTER TABLE users ADD COLUMN username VARCHAR(100)
        """))

        # 2. Popular username a partir de employee_name
        connection.execute(sa.text("""
            UPDATE users SET username = employee_name
        """))

        # 3. Tornar username NOT NULL e UNIQUE
        connection.execute(sa.text("""
            ALTER TABLE users ALTER COLUMN username SET NOT NULL
        """))
        connection.execute(sa.text("""
            CREATE UNIQUE INDEX ix_users_username ON users (username)
        """))

        # 4. Remover colunas novas
        connection.execute(sa.text("DROP INDEX IF EXISTS ix_users_user_number"))
        connection.execute(sa.text("ALTER TABLE users DROP COLUMN user_number"))
        connection.execute(sa.text("ALTER TABLE users DROP COLUMN employee_name"))
    finally:
        _disable_bypass(connection)