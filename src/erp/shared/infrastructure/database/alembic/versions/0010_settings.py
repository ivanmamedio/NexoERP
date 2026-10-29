"""Create settings table (company-scoped key-value configuration).

Adiciona a tabela settings para armazenar configurações por empresa
(nome, CNPJ, endereço, cabeçalho/rodapé do cupom, timeout de sessão).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0010_settings"
down_revision: str | None = "0009_force_admin_password_change"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(), nullable=False, server_default=""),
        sa.Column("value_type", sa.String(length=20), nullable=False, server_default="string"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_username", sa.String(length=100), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "key", name="uq_settings_company_key"),
    )
    op.create_index(op.f("ix_settings_company_id"), "settings", ["company_id"], unique=False)
    op.create_index(op.f("ix_settings_key"), "settings", ["key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_settings_key"), table_name="settings")
    op.drop_index(op.f("ix_settings_company_id"), table_name="settings")
    op.drop_table("settings")
