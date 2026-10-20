"""Remove problematic indexes and add optimized ones.

The ix_products_company_active_price index was causing pdv_sku_search to use
the wrong index (it matched company_id + active but didn't include sku).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "ecb057dd5ae5"
down_revision: str | None = "dbd3a80b7a22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove the problematic index that was hurting SKU lookups
    op.drop_index("ix_products_company_active_price", table_name="products")

    # Add a better composite index for SKU lookups (company + sku + active)
    op.create_index(
        "ix_products_company_sku_active",
        "products",
        ["company_id", "sku", "active"],
        unique=False,
    )

    # Add covering index for pdv name search (company + active + name)
    op.create_index(
        "ix_products_company_active_name",
        "products",
        ["company_id", "active", "name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_products_company_active_name", table_name="products")
    op.drop_index("ix_products_company_sku_active", table_name="products")
    # Re-create the removed index
    op.create_index(
        "ix_products_company_active_price",
        "products",
        ["company_id", "active", "cost_cents", "price_cents"],
        unique=False,
    )