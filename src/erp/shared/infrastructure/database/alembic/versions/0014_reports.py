"""Create reports table.

Revision ID: 0014_reports
Revises: 0013_credit_notebook
Create Date: 2026-11-18 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_reports"
down_revision = "0013_credit_notebook"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_type", sa.String(50), nullable=False, index=True),
        sa.Column("filter_params", sa.JSON(), nullable=False, default=dict),
        sa.Column("file_path", sa.String(500), nullable=False, default=""),
        sa.Column("file_format", sa.String(10), nullable=False, default=""),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("generated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("error_message", sa.String(), nullable=False, default=""),
    )


def downgrade() -> None:
    op.drop_table("reports")
