"""Force must_change_password=True for the existing admin user.

Elimina a possibilidade de senha padrão (admin/admin) em bancos de
desenvolvimento já criados. O admin existente será obrigado a trocar a
senha no próximo login.

Não edita migrações já aplicadas; esta é uma nova migração.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0009_force_admin_password_change"
down_revision: str | None = "ecb057dd5ae5"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Define must_change_password=1 para o usuário admin, se existir."""
    connection = op.get_bind()
    # Verifica se a tabela users existe (migração 0002 já a criou)
    inspector = sa.inspect(connection)
    if "users" not in inspector.get_table_names():
        return
    # Força troca de senha para o admin existente, se houver
    connection.execute(
        sa.text("UPDATE users SET must_change_password = 1 WHERE username = 'admin'")
    )


def downgrade() -> None:
    """Reverte: remove a força de troca de senha do admin."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "users" not in inspector.get_table_names():
        return
    connection.execute(
        sa.text("UPDATE users SET must_change_password = 0 WHERE username = 'admin'")
    )
