"""Composition root."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.config import paths as app_paths
from erp.config.logging_config import setup_logging
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.seed import create_first_admin, seed
from erp.shared.infrastructure.database.engine import build_engine
from erp.shared.infrastructure.database.migrations import run_migrations

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppContext:
    """Container for the services constructed at startup."""
    engine: Engine
    data_dir: Path
    db_path: Path


def bootstrap(*, data_dir: Path | None = None) -> AppContext:
    """Initialise logging, paths, database engine and run migrations."""
    resolved_data_dir = data_dir or app_paths.get_data_dir()
    resolved_data_dir.mkdir(parents=True, exist_ok=True)

    setup_logging()
    _logger.info("Starting ERP bootstrap (data_dir=%s)", resolved_data_dir)

    db_path = resolved_data_dir / "erp.db"
    engine = build_engine(db_path)

    # Migrations run synchronously at startup
    run_migrations(engine.url.render_as_string(hide_password=False))

    # Seed idempotente de papéis/primeiro admin (não faz nada se já existir)
    _logger.info("Seeding identity roles/permissions (if empty)")
    with Session(engine) as session:
        hasher = BcryptHasher()
        seed(session=session, password_hasher=hasher)
        admin_password = os.environ.get("NEXOERP_ADMIN_PASSWORD")
        if admin_password:
            username = os.environ.get("NEXOERP_ADMIN_USERNAME", "admin")
            create_first_admin(
                session=session,
                password_hasher=hasher,
                username=username,
                password=admin_password,
            )
            _logger.info("Initial admin ensured for user %r", username)

    return AppContext(engine=engine, data_dir=resolved_data_dir, db_path=db_path)
