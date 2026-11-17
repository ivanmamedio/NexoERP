"""Add performance indexes for Task 5.1 (load testing 50k products, 100k sales).

Based on load testing with 50k products and 100k sales, these indexes
improve slow queries in:
- Sales by period report (GROUP BY date, count DISTINCT)
- Sales by product report (GROUP BY product)
- Profit margin report (full table scan on products)
- PDV name search (ORDER BY optimization)

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "d3d407b12fb7"
down_revision: str | None = "6d9acc35f851"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Sales by period: optimize GROUP BY date(s.created_at) and count(DISTINCT s.id)
    # The covering index ix_sales_company_status_created_covering already exists
    # but we need a better index for the date-based grouping
    op.create_index(
        "ix_sales_company_created_date",
        "sales",
        ["company_id", "created_at"],
        unique=False,
    )

    # 2. Sales by product: optimize GROUP BY p.id with joins
    # Index on sale_items for the join path sales -> sale_items -> products
    op.create_index(
        "ix_sale_items_company_sale_product",
        "sale_items",
        ["company_id", "sale_id", "product_id"],
        unique=False,
    )

    # 3. Profit margin report: optimize full scan on products
    # The query filters by company_id, active=1 and orders by margin_percent
    # margin_percent is calculated: (price_cents - cost_cents) * 100 / price_cents
    # We add an index that helps filter and sort
    op.create_index(
        "ix_products_company_active_price_margin",
        "products",
        ["company_id", "active", "price_cents", "cost_cents"],
        unique=False,
    )

    # 4. PDV name search: optimize ORDER BY name for prefix search
    # The index ix_products_company_name_nocase exists but we need to help with ORDER BY
    # SQLite can use the index for ORDER BY if the WHERE uses the same prefix
    # This is already covered by ix_products_company_name_nocase

    # 5. Sales by operator: optimize GROUP BY operator
    op.create_index(
        "ix_sales_company_user_created",
        "sales",
        ["company_id", "user_id", "created_at"],
        unique=False,
    )

    # 6. Cash closing: optimize queries on cash_sessions by register and date
    op.create_index(
        "ix_cash_sessions_register_opened",
        "cash_sessions",
        ["register_id", "opened_at"],
        unique=False,
    )

    # 7. Treasury cash flow: optimize financial_entries by company and date
    # The index ix_financial_entries_company_type_date exists but we add a covering one
    op.create_index(
        "ix_financial_entries_company_date_amount",
        "financial_entries",
        ["company_id", "date", "amount_cents"],
        unique=False,
    )

    # 8. Low stock: the index ix_products_company_active_min_stock_qty exists
    # but we ensure it covers the ORDER BY current_stock ASC
    # (already covered)

    # 9. Stock movements: optimize inventory reports by product and date
    # Index ix_stock_movements_company_product_date exists
    pass


def downgrade() -> None:
    op.drop_index("ix_financial_entries_company_date_amount", table_name="financial_entries")
    op.drop_index("ix_cash_sessions_register_opened", table_name="cash_sessions")
    op.drop_index("ix_sales_company_user_created", table_name="sales")
    op.drop_index("ix_products_company_active_price_margin", table_name="products")
    op.drop_index("ix_sale_items_company_sale_product", table_name="sale_items")
    op.drop_index("ix_sales_company_created_date", table_name="sales")
