"""Integration test: bootstrap creates the DB from scratch and honours PRAGMAs."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text

from erp.bootstrap import bootstrap


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "erp_data"


def test_bootstrap_creates_db_with_required_pragmas(data_dir: Path) -> None:
    ctx = bootstrap(data_dir=data_dir)
    assert ctx.db_path.exists(), "Database file must be created by bootstrap"

    with ctx.engine.connect() as conn:
        journal_mode = conn.execute(text("PRAGMA journal_mode;")).scalar_one()
        foreign_keys = conn.execute(text("PRAGMA foreign_keys;")).scalar_one()
        busy_timeout = conn.execute(text("PRAGMA busy_timeout;")).scalar_one()

    assert journal_mode.lower() == "wal"
    assert int(foreign_keys) == 1
    assert int(busy_timeout) >= 5000


def test_bootstrap_is_idempotent(data_dir: Path) -> None:
    """Running bootstrap twice must not fail or corrupt the database."""
    first = bootstrap(data_dir=data_dir)
    second = bootstrap(data_dir=data_dir)
    assert first.db_path == second.db_path
    assert first.db_path.exists()


def test_bootstrap_creates_pdv_indexes(data_dir: Path) -> None:
    """A migração 0009 deve criar os índices usados pelo PDV."""
    ctx = bootstrap(data_dir=data_dir)
    with ctx.engine.connect() as conn:
        names = {
            row[0]
            for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type = 'index'"))
        }
    assert "ix_products_company_name_nocase" in names
    assert "ix_products_company_sku" in names
