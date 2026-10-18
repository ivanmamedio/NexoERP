"""Create companies table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_companies"
down_revision: str | None = "0002_identity_tables"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("trade_name", sa.String(length=200), nullable=False),
        sa.Column("tax_id", sa.String(length=20), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_companies_company_id"), "companies", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_companies_name"), "companies", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_companies_tax_id"), "companies", ["tax_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_companies_tax_id"), table_name="companies")
    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_index(op.f("ix_companies_company_id"), table_name="companies")
    op.drop_table("companies")
