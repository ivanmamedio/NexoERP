"""Create backups table for backup metadata.

Adiciona a tabela backups para registro de metadados de backups
realizados (arquivo, checksum, data, tipo, etc.).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0011_backups"
down_revision: str | None = "0010_settings"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "backups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("backup_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=False, default=""),
        sa.Column("source_db_path", sa.String(length=500), nullable=False),
        sa.Column("rotation_tag", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backups_backup_type"), "backups", ["backup_type"], unique=False)
    op.create_index(op.f("ix_backups_status"), "backups", ["status"], unique=False)
    op.create_index(op.f("ix_backups_rotation_tag"), "backups", ["rotation_tag"], unique=False)
    op.create_index(op.f("ix_backups_started_at"), "backups", ["started_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_backups_started_at"), table_name="backups")
    op.drop_index(op.f("ix_backups_rotation_tag"), table_name="backups")
    op.drop_index(op.f("ix_backups_status"), table_name="backups")
    op.drop_index(op.f("ix_backups_backup_type"), table_name="backups")
    op.drop_table("backups")
