"""Add expression index for profit margin report.

The profit_margin report query filters by company_id AND active=1, then
orders by margin_percent which is a calculated expression, not a stored
column. The existing index ix_products_company_active_price_margin helps
with the WHERE clause but not with ORDER BY margin_percent DESC, causing
a full table sort on 50k products.

This migration adds an expression index so SQLite can both filter and
sort using the index, avoiding the TEMP B-TREE sort.

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015_profit_margin_index"
down_revision: str | None = "0014_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Expression index for profit margin report:
    # WHERE company_id=? AND active=? ORDER BY margin_percent DESC
    # margin_percent = (price_cents - cost_cents) * 100.0 / price_cents
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_company_active_margin_expr "
        "ON products (company_id, active, ((price_cents - cost_cents) * 100.0 / price_cents))"
    )


def downgrade() -> None:
    op.drop_index("ix_products_company_active_margin_expr", table_name="products")
