"""Add credit notebook tables.

Revision ID: 0013_credit_notebook
Revises: d3d407b12fb7
Create Date: 2026-11-18 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "0013_credit_notebook"
down_revision = "d3d407b12fb7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Credit customers table
    op.create_table(
        "credit_customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, index=True),
        sa.Column("phone", sa.String(20), nullable=False, index=True),
        sa.Column("email", sa.String(200), nullable=False, default=""),
        sa.Column("address", sa.Text(), nullable=False, default=""),
        sa.Column("notes", sa.Text(), nullable=False, default=""),
        sa.Column("credit_limit_cents", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(20), nullable=False, default="active", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_credit_customers_company_phone", "credit_customers", ["company_id", "phone"])
    op.create_index("ix_credit_customers_company_name", "credit_customers", ["company_id", "name"])

    # Credit entries table
    op.create_table(
        "credit_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("credit_customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("entry_type", sa.String(20), nullable=False, default="charge", index=True),
        sa.Column("description", sa.String(500), nullable=False, default=""),
        sa.Column("amount_cents", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_amount_cents", sa.Integer(), nullable=False, default=0),
        sa.Column("reference_type", sa.String(50), nullable=False, default=""),
        sa.Column("reference_id", sa.Integer(), nullable=True, index=True),
        sa.Column("notes", sa.Text(), nullable=False, default=""),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(100), nullable=False, default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("credit_entries")
    op.drop_table("credit_customers")