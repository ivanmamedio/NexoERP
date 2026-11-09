"""Create payables, receivables, and financial_categories tables

Revision ID: 6d9acc35f851
Revises: d65f299c1ba6
Create Date: 2026-11-08 22:48:08.370997
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6d9acc35f851"
down_revision: str | None = "d65f299c1ba6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # financial_categories
    op.create_table(
        "financial_categories",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),  # expense, income, transfer
        sa.Column("description", sa.String(), nullable=False, default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
    )

    # payables
    op.create_table(
        "payables",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("supplier_id", sa.Integer(), nullable=True, index=True),
        sa.Column("category_id", sa.Integer(), nullable=True, index=True),
        sa.Column("description", sa.String(), nullable=False, default=""),
        sa.Column("total_amount_cents", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column(
            "issue_date",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
        sa.Column("recurrence_type", sa.String(20), nullable=False, default="none"),
        sa.Column("recurrence_count", sa.Integer(), nullable=False, default=1),
        sa.Column("source_type", sa.String(50), nullable=False, default=""),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
    )

    # payable_installments
    op.create_table(
        "payable_installments",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column(
            "payable_id",
            sa.Integer(),
            sa.ForeignKey("payables.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("installment_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("paid_amount_cents", sa.Integer(), nullable=False, default=0),
    )

    # receivables
    op.create_table(
        "receivables",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("customer_id", sa.Integer(), nullable=True, index=True),
        sa.Column("category_id", sa.Integer(), nullable=True, index=True),
        sa.Column("description", sa.String(), nullable=False, default=""),
        sa.Column("total_amount_cents", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column(
            "issue_date",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("received_amount_cents", sa.Integer(), nullable=False, default=0),
        sa.Column("source_type", sa.String(50), nullable=False, default=""),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("datetime('now')"),
        ),
    )


def downgrade() -> None:
    op.drop_table("receivables")
    op.drop_table("payable_installments")
    op.drop_table("payables")
    op.drop_table("financial_categories")
