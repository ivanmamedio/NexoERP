"""Create initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

Baseline revision. The ``alembic_version`` table is created and managed by
Alembic itself, so a migration must never create or drop it.
"""
from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Baseline: nothing to create."""


def downgrade() -> None:
    """Baseline: nothing to drop."""
