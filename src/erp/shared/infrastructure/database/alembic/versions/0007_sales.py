"""Create sales tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0007_sales"
down_revision: str | None = "0006_cash"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("discount_cents", sa.Integer(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("paid_cents", sa.Integer(), nullable=False),
        sa.Column("change_cents", sa.Integer(), nullable=False),
        sa.Column("cancel_reason", sa.String(), nullable=False),
        sa.Column("cancelled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("cancelled_by_username", sa.String(length=100), nullable=False),
        sa.Column("authorized_by_user_id", sa.Integer(), nullable=True),
        sa.Column("authorized_by_username", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_company_id", "sales", ["company_id"], unique=False)
    op.create_index("ix_sales_status", "sales", ["status"], unique=False)
    op.create_index("ix_sales_session_id", "sales", ["session_id"], unique=False)

    op.create_table(
        "sale_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("quantity_thousandths", sa.Integer(), nullable=False),
        sa.Column("line_total_cents", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=10), nullable=False),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.Column("cancel_reason", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], name="fk_sale_items_sale_id"),
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"], unique=False)

    op.create_table(
        "sale_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("change_cents", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["sale_id"], ["sales.id"], name="fk_sale_payments_sale_id"
        ),
    )
    op.create_index("ix_sale_payments_sale_id", "sale_payments", ["sale_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sale_payments_sale_id", table_name="sale_payments")
    op.drop_table("sale_payments")
    op.drop_index("ix_sale_items_sale_id", table_name="sale_items")
    op.drop_table("sale_items")
    op.drop_index("ix_sales_session_id", table_name="sales")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_index("ix_sales_company_id", table_name="sales")
    op.drop_table("sales")
