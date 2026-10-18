"""Create cash tables (cash_registers, cash_sessions, cash_movements)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_cash"
down_revision: str | None = "0005_catalog"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "cash_registers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("terminal_code", sa.String(length=50), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cash_registers_company_id"), "cash_registers", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_cash_registers_terminal_code"), "cash_registers", ["terminal_code"], unique=False
    )

    op.create_table(
        "cash_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("register_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("opened_by_user_id", sa.Integer(), nullable=True),
        sa.Column("opened_by_username", sa.String(length=100), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("opening_amount_cents", sa.Integer(), nullable=False),
        sa.Column("closed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("closed_by_username", sa.String(length=100), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("closing_amount_cents", sa.Integer(), nullable=False),
        sa.Column("total_sales_cents", sa.Integer(), nullable=False),
        sa.Column("total_suprimentos_cents", sa.Integer(), nullable=False),
        sa.Column("total_sangrias_cents", sa.Integer(), nullable=False),
        sa.Column("total_pix_cents", sa.Integer(), nullable=False),
        sa.Column("total_card_cents", sa.Integer(), nullable=False),
        sa.Column("expected_cash_cents", sa.Integer(), nullable=False),
        sa.Column("difference_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("blind_close", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["register_id"], ["cash_registers.id"], name="fk_cash_sessions_register_id"
        ),
    )
    op.create_index(
        op.f("ix_cash_sessions_register_id"), "cash_sessions", ["register_id"], unique=False
    )
    op.create_index(
        op.f("ix_cash_sessions_company_id"), "cash_sessions", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_cash_sessions_status"), "cash_sessions", ["status"], unique=False
    )

    op.create_table(
        "cash_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["cash_sessions.id"], name="fk_cash_movements_session_id"
        ),
    )
    op.create_index(
        op.f("ix_cash_movements_session_id"), "cash_movements", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_cash_movements_company_id"), "cash_movements", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_cash_movements_movement_type"), "cash_movements", ["movement_type"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_cash_movements_movement_type"), table_name="cash_movements")
    op.drop_index(op.f("ix_cash_movements_company_id"), table_name="cash_movements")
    op.drop_index(op.f("ix_cash_movements_session_id"), table_name="cash_movements")
    op.drop_table("cash_movements")
    op.drop_index(op.f("ix_cash_sessions_status"), table_name="cash_sessions")
    op.drop_index(op.f("ix_cash_sessions_company_id"), table_name="cash_sessions")
    op.drop_index(op.f("ix_cash_sessions_register_id"), table_name="cash_sessions")
    op.drop_table("cash_sessions")
    op.drop_index(op.f("ix_cash_registers_terminal_code"), table_name="cash_registers")
    op.drop_index(op.f("ix_cash_registers_company_id"), table_name="cash_registers")
    op.drop_table("cash_registers")
