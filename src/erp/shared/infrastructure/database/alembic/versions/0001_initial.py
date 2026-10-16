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
