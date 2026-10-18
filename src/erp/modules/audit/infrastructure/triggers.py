"""SQLite triggers that enforce the audit trail append-only policy.

Triggers block UPDATE and DELETE on business tables so records cannot be
altered outside the audit system. A bypass table (``audit_bypass``) lets a
legitimate transaction temporarily enable writes when the application needs
to correct data through its own Unit of Work.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Tables protected against direct UPDATE/DELETE outside the audit system.
_PROTECTED_TABLES = ("users", "roles", "permissions", "companies")

_BYPASS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS audit_bypass (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO audit_bypass (id, enabled) VALUES (1, 0);
"""

_ENABLE_BYPASS = "UPDATE audit_bypass SET enabled = 1 WHERE id = 1"
_DISABLE_BYPASS = "UPDATE audit_bypass SET enabled = 0 WHERE id = 1"


def _block_trigger_ddl(table: str) -> str:
    name_update = f"block_update_{table}"
    name_delete = f"block_delete_{table}"
    return f"""
CREATE TRIGGER IF NOT EXISTS {name_update}
BEFORE UPDATE ON {table}
BEGIN
    SELECT CASE WHEN (SELECT enabled FROM audit_bypass WHERE id = 1) = 0
        THEN RAISE(ABORT, 'UPDATE blocked by audit trigger on {table}')
    END;
END;
CREATE TRIGGER IF NOT EXISTS {name_delete}
BEFORE DELETE ON {table}
BEGIN
    SELECT CASE WHEN (SELECT enabled FROM audit_bypass WHERE id = 1) = 0
        THEN RAISE(ABORT, 'DELETE blocked by audit trigger on {table}')
    END;
END;
"""


def _drop_trigger_ddl(table: str) -> str:
    return f"""
DROP TRIGGER IF EXISTS block_update_{table};
DROP TRIGGER IF EXISTS block_delete_{table};
"""


def install_triggers(engine: Engine) -> None:
    """Create the bypass table and install UPDATE/DELETE blocking triggers."""
    with engine.begin() as connection:
        connection.execute(text(_BYPASS_TABLE_DDL))
        for table in _PROTECTED_TABLES:
            connection.execute(text(_block_trigger_ddl(table)))


def uninstall_triggers(engine: Engine) -> None:
    """Remove all audit blocking triggers."""
    with engine.begin() as connection:
        for table in _PROTECTED_TABLES:
            connection.execute(text(_drop_trigger_ddl(table)))


def enable_bypass(engine: Engine) -> None:
    """Allow UPDATE/DELETE on protected tables within the current flow."""
    with engine.begin() as connection:
        connection.execute(text(_ENABLE_BYPASS))


def disable_bypass(engine: Engine) -> None:
    """Re-enable UPDATE/DELETE blocking on protected tables."""
    with engine.begin() as connection:
        connection.execute(text(_DISABLE_BYPASS))
