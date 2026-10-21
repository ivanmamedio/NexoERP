"""Create treasury tables (financial_entries)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0008_treasury"
down_revision: str | None = "0007_sales"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "financial_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_financial_entries_company_id"),
        "financial_entries",
        ["company_id"],
        unique=False,
    )
    op.create_index(op.f("ix_financial_entries_type"), "financial_entries", ["type"], unique=False)
    op.create_index(
        op.f("ix_financial_entries_source_type"),
        "financial_entries",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_entries_source_id"),
        "financial_entries",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_entries_source_id"), table_name="financial_entries")
    op.drop_index(op.f("ix_financial_entries_source_type"), table_name="financial_entries")
    op.drop_index(op.f("ix_financial_entries_type"), table_name="financial_entries")
    op.drop_index(op.f("ix_financial_entries_company_id"), table_name="financial_entries")
    op.drop_table("financial_entries")
