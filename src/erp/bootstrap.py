"""Composition root."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.config import paths as app_paths
from erp.config.logging_config import setup_logging
from erp.modules.audit.application.event_subscriber import AuditEventSubscriber
from erp.modules.audit.application.services import AuditService
from erp.modules.audit.infrastructure.triggers import install_triggers
from erp.modules.backup.application.service import BackupService
from erp.modules.backup.infrastructure.repository import SqlAlchemyBackupRepository
from erp.modules.backup.infrastructure.scheduler import BackupScheduler
from erp.modules.cash.application.sale_subscriber import CashSaleSubscriber
from erp.modules.cash.application.services import CashServices
from erp.modules.catalog.application.sale_subscriber import CatalogSaleSubscriber
from erp.modules.catalog.application.services import SqlAlchemyCatalogServices
from erp.modules.catalog.infrastructure.price_updater import CatalogPriceUpdater
from erp.modules.catalog.infrastructure.repository import SqlAlchemyProductRepository
from erp.modules.catalog.infrastructure.unit_of_work import SqlAlchemyCatalogUnitOfWork
from erp.modules.companies.application.services import CompaniesServices
from erp.modules.companies.infrastructure.permission_checker import SqlAlchemyPermissionChecker
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import SqlAlchemyUserRepository
from erp.modules.identity.infrastructure.seed import create_first_admin, seed
from erp.modules.pricing.application.services import PricingServices
from erp.modules.sales.application.ports import CatalogUnitOfWork
from erp.modules.sales.application.services import SalesServices
from erp.modules.treasury.application.cash_subscriber import TreasuryCashSubscriber
from erp.modules.treasury.application.sale_subscriber import TreasurySaleSubscriber
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
    sales_services: SalesServices | None = None
    backup_service: BackupService | None = None
    backup_scheduler: BackupScheduler | None = None
    event_bus: EventBus | None = None


def _catalog_uow_factory(engine: Engine) -> Callable[[], CatalogUnitOfWork]:
    """Factory for catalog unit of work (for sales module dependency inversion)."""
    return lambda: SqlAlchemyCatalogUnitOfWork(engine)  # type: ignore[return-value]


def _product_repo_factory(engine: Engine) -> Callable[[], SqlAlchemyProductRepository]:
    """Factory for creating product repository within a catalog UoW."""
    def factory() -> SqlAlchemyProductRepository:
        uow = SqlAlchemyCatalogUnitOfWork(engine)
        uow.__enter__()
        products = uow.products
        assert products is not None
        return products
    return factory


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

    # Subscribers que reagem a SaleCompleted (catalog, cash, treasury)
    CatalogSaleSubscriber(event_bus=event_bus, engine=engine)
    CashSaleSubscriber(event_bus=event_bus, engine=engine)
    TreasurySaleSubscriber(event_bus=event_bus, engine=engine)

    # Subscriber que reage a eventos de caixa (sangria, suprimento, abertura, fechamento)
    TreasuryCashSubscriber(event_bus=event_bus, engine=engine)

    # Catalog services (permissions are checked per-use-case; no logged-in user yet)
    catalog_services = SqlAlchemyCatalogServices(
        engine=engine,
        event_bus=event_bus,
        user_permissions=set(),
    )

    # Price updater for pricing module (dependency inversion)
    price_updater = CatalogPriceUpdater(
        product_repo_factory=_product_repo_factory(engine),
        event_bus=event_bus,
        user_permissions=set(),
    )

    # Companies services with permission gate
    with Session(engine) as session:
        user_repo = SqlAlchemyUserRepository(session)
        permission_checker = SqlAlchemyPermissionChecker(user_repo)
        from erp.modules.companies.application.permission_gate import CompanyPermissionGate
        permission_gate = CompanyPermissionGate(permission_checker)
    companies_services = CompaniesServices(engine=engine, permission_gate=permission_gate)

    # Pricing services (uses price_updater port)
    pricing_services = PricingServices(engine=engine, price_updater=price_updater)

    # Cash services (permissions are checked per-use-case; no logged-in user yet)
    cash_services = CashServices(engine=engine)

    # Sales services (uses catalog UoW factory for dependency inversion)
    sales_services = SalesServices(
        engine=engine,
        catalog_uow_factory=_catalog_uow_factory(engine),
        event_bus=event_bus,
        user_permissions=set(),
    )

    # Backup services
    backup_repo = SqlAlchemyBackupRepository(Session(engine))
    backup_dir = resolved_data_dir / "backups"
    secondary_dir = Path(os.environ.get("NEXOERP_BACKUP_SECONDARY", "")) or None
    backup_service = BackupService(
        repo=backup_repo,
        backup_dir=backup_dir,
        secondary_dir=Path(secondary_dir) if secondary_dir else None,
    )

    # Backup scheduler
    scheduler = BackupScheduler()

    def _daily_backup_callback() -> None:
        backup_service.create_backup("daily", str(db_path), "daily")

    def _monthly_backup_callback() -> None:
        backup_service.create_backup("monthly", str(db_path), "monthly")

    scheduler.schedule_daily_backup("02:00", _daily_backup_callback)
    scheduler.schedule_monthly_backup(1, "03:00", _monthly_backup_callback)
    scheduler.start()

    return AppContext(
        engine=engine,
        data_dir=resolved_data_dir,
        db_path=db_path,
        companies_services=companies_services,
        audit_services=audit_services,
        catalog_services=catalog_services,
        pricing_services=pricing_services,
        cash_services=cash_services,
        sales_services=sales_services,
        backup_service=backup_service,
        backup_scheduler=scheduler,
        event_bus=event_bus,
    )