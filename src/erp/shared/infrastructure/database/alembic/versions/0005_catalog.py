"""Create catalog tables (categories, suppliers, products, stock_movements, price_histories)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_catalog"
down_revision: str | None = "0004_audit_logs"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_categories_company_id"), "categories", ["company_id"], unique=False)
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("trade_name", sa.String(length=200), nullable=False),
        sa.Column("tax_id", sa.String(length=20), nullable=False),
        sa.Column("contact_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_company_id"), "suppliers", ["company_id"], unique=False)
    op.create_index(op.f("ix_suppliers_name"), "suppliers", ["name"], unique=False)
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("unit", sa.String(length=10), nullable=False),
        sa.Column("cost_cents", sa.Integer(), nullable=False),
        sa.Column("margin_pct", sa.Integer(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("min_stock_qty", sa.Integer(), nullable=False),
        sa.Column("stock_qty", sa.Integer(), nullable=False),
        sa.Column("sold_by_weight", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_company_id"), "products", ["company_id"], unique=False)
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=False)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("quantity_thousandths", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], name="fk_stock_movements_product_id"
        ),
    )
    op.create_index(
        op.f("ix_stock_movements_product_id"),
        "stock_movements",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_movements_company_id"),
        "stock_movements",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_movements_created_at"),
        "stock_movements",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "price_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("old_price_cents", sa.Integer(), nullable=False),
        sa.Column("new_price_cents", sa.Integer(), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("changed_by_username", sa.String(length=100), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], name="fk_price_histories_product_id"
        ),
    )
    op.create_index(
        op.f("ix_price_histories_product_id"),
        "price_histories",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_price_histories_company_id"),
        "price_histories",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_price_histories_changed_at"),
        "price_histories",
        ["changed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_price_histories_changed_at"), table_name="price_histories")
    op.drop_index(op.f("ix_price_histories_company_id"), table_name="price_histories")
    op.drop_index(op.f("ix_price_histories_product_id"), table_name="price_histories")
    op.drop_table("price_histories")
    op.drop_index(op.f("ix_stock_movements_created_at"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_company_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_product_id"), table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index(op.f("ix_products_name"), table_name="products")
    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.drop_index(op.f("ix_products_company_id"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_suppliers_name"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_company_id"), table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_index(op.f("ix_categories_company_id"), table_name="categories")
    op.drop_table("categories")
