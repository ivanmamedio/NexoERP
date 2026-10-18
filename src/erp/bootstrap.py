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
from erp.modules.audit.application.event_subscriber import AuditEventSubscriber
from erp.modules.audit.application.services import AuditService
from erp.modules.audit.infrastructure.triggers import install_triggers
from erp.modules.cash.application.services import CashServices
from erp.modules.catalog.application.services import SqlAlchemyCatalogServices
from erp.modules.companies.application.services import CompaniesServices
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.seed import create_first_admin, seed
from erp.modules.pricing.application.services import PricingServices
from erp.shared.application.events import EventBus
from erp.shared.infrastructure.database.engine import build_engine
from erp.shared.infrastructure.database.migrations import run_migrations

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppContext:
    """Container for the services constructed at startup."""
    engine: Engine
    data_dir: Path
    db_path: Path
    companies_services: CompaniesServices | None = None
    audit_services: AuditService | None = None
    catalog_services: SqlAlchemyCatalogServices | None = None
    pricing_services: PricingServices | None = None
    cash_services: CashServices | None = None
    event_bus: EventBus | None = None


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

    # Install audit triggers (block direct UPDATE/DELETE on business tables)
    install_triggers(engine)

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

    # Audit services + EventBus subscriber
    event_bus = EventBus()
    audit_services = AuditService(engine)
    AuditEventSubscriber(event_bus=event_bus, audit_service=audit_services)

    # Catalog services (permissions are checked per-use-case; no logged-in user yet)
    catalog_services = SqlAlchemyCatalogServices(
        engine=engine,
        event_bus=event_bus,
        user_permissions=set(),
    )

    # Pricing services
    pricing_services = PricingServices(engine=engine, catalog_services=catalog_services)

    # Cash services (permissions are checked per-use-case; no logged-in user yet)
    cash_services = CashServices(engine=engine)

    return AppContext(
        engine=engine,
        data_dir=resolved_data_dir,
        db_path=db_path,
        companies_services=CompaniesServices(engine),
        audit_services=audit_services,
        catalog_services=catalog_services,
        pricing_services=pricing_services,
        cash_services=cash_services,
        event_bus=event_bus,
    )
