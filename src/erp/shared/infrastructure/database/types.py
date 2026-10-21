"""Custom SQLAlchemy column types."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


def _utcnow() -> datetime:
    """Retorna o momento atual em UTC (aware). Usado como default de colunas."""
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """DateTime that is always timezone-aware (UTC) in Python.

    SQLite has no timezone support and returns naive datetimes. This type
    stores UTC wall-clock values and rebuilds aware UTC datetimes on read, so
    comparisons with ``datetime.now(UTC)`` never raise ``TypeError``.
    The DDL is still a plain DATETIME, so no migration is required.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)
