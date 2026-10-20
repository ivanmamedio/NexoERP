"""Add composite indexes used by the PDV (name search and SKU lookup)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0009_pos_indexes"
down_revision: str | None = "0008_treasury"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Case-insensitive prefix search by name, always scoped by company.
    op.create_index(
        "ix_products_company_name_nocase",
        "products",
        ["company_id", sa.text("name COLLATE NOCASE")],
        unique=False,
    )
    # Barcode/SKU lookup scoped by company.
    op.create_index(
        "ix_products_company_sku",
        "products",
        ["company_id", "sku"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_products_company_sku", table_name="products")
    op.drop_index("ix_products_company_name_nocase", table_name="products")
