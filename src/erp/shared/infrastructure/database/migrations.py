"""Programmatic Alembic runner."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

_logger = logging.getLogger(__name__)
_ALEMBIC_DIR = Path(__file__).resolve().parent / "alembic"


def _build_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("logging.level.root", "WARNING")
    return cfg


def run_migrations(db_url: str, *, revision: str = "head") -> None:
    """Apply Alembic migrations up to revision (default head)."""
    cfg = _build_config(db_url)
    _logger.info("Running database migrations (target=%s)", revision)
    try:
        command.upgrade(cfg, revision)
    except Exception:
        _logger.exception("Database migration failed")
        raise
