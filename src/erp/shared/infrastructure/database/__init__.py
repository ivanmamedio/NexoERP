"""Database infrastructure: engine, session factory, and declarative base."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import DateTime

from erp.config.paths import get_data_dir
from erp.shared.infrastructure.database.engine import build_engine


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


def get_engine() -> Engine:
    """Create the default engine using the platform data directory."""
    data_dir = get_data_dir()
    db_path = data_dir / "erp.db"
    return build_engine(db_path)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


__all__ = ["Base", "build_engine", "get_engine", "get_session_factory"]
