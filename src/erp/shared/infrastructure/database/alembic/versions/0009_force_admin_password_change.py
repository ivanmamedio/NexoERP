"""Force must_change_password=True for the existing admin user.

Elimina a possibilidade de senha padrão (admin/admin) em bancos de
desenvolvimento já criados. O admin existente será obrigado a trocar a
senha no próximo login.

Não edita migrações já aplicadas; esta é uma nova migração.
"""

from __future__ import annotations

import contextlib

import sqlalchemy as sa
from alembic import op

revision: str = "0009_force_admin_password_change"
down_revision: str | None = "ecb057dd5ae5"
branch_labels: str | None = None
depends_on: str | None = None

_BYPASS_ENABLE = "UPDATE audit_bypass SET enabled = 1 WHERE id = 1"
_BYPASS_DISABLE = "UPDATE audit_bypass SET enabled = 0 WHERE id = 1"


def _enable_bypass(connection: sa.Connection) -> None:
    """Habilita bypass de auditoria para permitir UPDATE em tabelas protegidas."""
    with contextlib.suppress(Exception):
        connection.execute(sa.text(_BYPASS_ENABLE))


def _disable_bypass(connection: sa.Connection) -> None:
    """Reabilita bloqueio de auditoria."""
    with contextlib.suppress(Exception):
        connection.execute(sa.text(_BYPASS_DISABLE))


def upgrade() -> None:
    """Define must_change_password=1 para o usuário admin, se existir."""
    connection = op.get_bind()
    # Verifica se a tabela users existe (migração 0002 já a criou)
    inspector = sa.inspect(connection)
    if "users" not in inspector.get_table_names():
        return
    # Habilita bypass de auditoria para permitir o UPDATE
    _enable_bypass(connection)
    try:
        # Força troca de senha para o admin existente, se houver
        connection.execute(
            sa.text("UPDATE users SET must_change_password = 1 WHERE username = 'admin'")
        )
    finally:
        # Sempre reabilita o bloqueio
        _disable_bypass(connection)


def downgrade() -> None:
    """Reverte: remove a força de troca de senha do admin."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "users" not in inspector.get_table_names():
        return
    _enable_bypass(connection)
    try:
        connection.execute(
            sa.text("UPDATE users SET must_change_password = 0 WHERE username = 'admin'")
        )
    finally:
        _disable_bypass(connection)
