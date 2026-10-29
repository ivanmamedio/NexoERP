"""Application paths using platformdirs."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir, user_log_dir

_APP_NAME = "NexoERP"
_APP_AUTHOR = "NexoERP"


def get_data_dir() -> Path:
    """Return the platform-specific data directory."""
    return Path(user_data_dir(appname=_APP_NAME, appauthor=_APP_AUTHOR))


def get_logs_dir() -> Path:
    """Return the platform-specific log directory."""
    return Path(user_log_dir(appname=_APP_NAME, appauthor=_APP_AUTHOR))


def db_path() -> Path:
    """Return the default database path."""
    return get_data_dir() / "erp.db"
