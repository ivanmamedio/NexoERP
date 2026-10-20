"""Add performance indexes for reports and common queries.

Based on load testing with 50k products and 100k sales, these indexes
improve slow queries in reports (sales_by_period, profit_margin, low_stock).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "dbd3a80b7a22"
down_revision: str | None = "0009_pos_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Sales table: optimize sales_by_period report (filter by company, date range, status)
    op.create_index(
        "ix_sales_company_status_created",
        "sales",
        ["company_id", "status", "created_at"],
        unique=False,
    )

    # Sales table: optimize cash closing and session queries
    op.create_index(
        "ix_sales_company_session_created",
        "sales",
        ["company_id", "session_id", "created_at"],
        unique=False,
    )

    # Sale items: optimize sales reports joining with products
    op.create_index(
        "ix_sale_items_sale_company",
        "sale_items",
        ["sale_id", "company_id"],
        unique=False,
    )

    # Products: optimize low_stock report (filter by company, active, min_stock)
    op.create_index(
        "ix_products_company_active_min_stock",
        "products",
        ["company_id", "active", "min_stock_qty", "stock_qty"],
        unique=False,
    )

    # Products: optimize profit_margin report (filter by company, active)
    op.create_index(
        "ix_products_company_active_price",
        "products",
        ["company_id", "active", "cost_cents", "price_cents"],
        unique=False,
    )

    # Financial entries: optimize DRE and treasury reports
    op.create_index(
        "ix_financial_entries_company_type_date",
        "financial_entries",
        ["company_id", "type", "date"],
        unique=False,
    )

    # Cash sessions: optimize cash closing report
    op.create_index(
        "ix_cash_sessions_company_status_closed",
        "cash_sessions",
        ["company_id", "status", "closed_at"],
        unique=False,
    )

    # Stock movements: optimize inventory reports
    op.create_index(
        "ix_stock_movements_company_product_date",
        "stock_movements",
        ["company_id", "product_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_company_product_date", table_name="stock_movements")
    op.drop_index("ix_cash_sessions_company_status_closed", table_name="cash_sessions")
    op.drop_index("ix_financial_entries_company_type_date", table_name="financial_entries")
    op.drop_index("ix_products_company_active_price", table_name="products")
    op.drop_index("ix_products_company_active_min_stock", table_name="products")
    op.drop_index("ix_sale_items_sale_company", table_name="sale_items")
    op.drop_index("ix_sales_company_session_created", table_name="sales")
    op.drop_index("ix_sales_company_status_created", table_name="sales")