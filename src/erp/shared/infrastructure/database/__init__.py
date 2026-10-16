"""Database infrastructure: engine, session factory, and declarative base."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from erp.config.paths import get_data_dir
from erp.shared.infrastructure.database.engine import build_engine


Base = declarative_base()


def get_engine() -> Engine:
    """Create the default engine using the platform data directory."""
    data_dir = get_data_dir()
    db_path = data_dir / "erp.db"
    return build_engine(db_path)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


__all__ = ["Base", "build_engine", "get_engine", "get_session_factory"]
