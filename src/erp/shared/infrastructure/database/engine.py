"""SQLite engine factory with the PRAGMAs required by the project."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Engine


def _apply_pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()


def build_engine(db_path: Path) -> Engine:
    """Create an engine for db_path and register the PRAGMA hook."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Use SQLAlchemy URL.create() to handle Windows paths correctly (avoids C%3A encoding)
    url = URL.create("sqlite", database=str(db_path.resolve()))
    engine = create_engine(url, future=True)
    event.listen(engine, "connect", _apply_pragmas)
    return engine


__all__ = ["build_engine"]
