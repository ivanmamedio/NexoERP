"""Add performance indexes for reports and PDV search

Revision ID: d65f299c1ba6
Revises: 8706cf5235a7
Create Date: 2026-11-08 20:32:56.129423
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "d65f299c1ba6"
down_revision: str | None = "8706cf5235a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use raw SQL with IF NOT EXISTS for SQLite compatibility
    # Covering index for sales_by_period report query:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sales_company_status_created_covering "
        "ON sales (company_id, status, created_at, id, total_cents)"
    )

    # Composite index for sale_items join in reports:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sale_items_company_sale_id "
        "ON sale_items (company_id, sale_id)"
    )

    # Index for low stock report with category join
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_company_active_min_stock_qty "
        "ON products (company_id, active, min_stock_qty, stock_qty, category_id)"
    )

    # Covering index for financial_entries DRE query:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_financial_entries_company_type_date_covering "
        "ON financial_entries (company_id, type, date, amount_cents, category_id)"
    )


def downgrade() -> None:
    op.drop_index("ix_sales_company_status_created_covering", table_name="sales")
    op.drop_index("ix_sale_items_company_sale_id", table_name="sale_items")
    op.drop_index("ix_products_company_active_min_stock_qty", table_name="products")
    op.drop_index("ix_financial_entries_company_type_date_covering", table_name="financial_entries")
