"""SQLAlchemy Unit of Work for the catalog module."""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.modules.catalog.infrastructure.repository import (
    SqlAlchemyCategoryRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyStockMovementRepository,
    SqlAlchemySupplierRepository,
)
from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemyCatalogUnitOfWork(UnitOfWork):
    """Unit of Work implementation for catalog using a single session."""

    def __init__(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self.products: SqlAlchemyProductRepository | None = None
        self.categories: SqlAlchemyCategoryRepository | None = None
        self.suppliers: SqlAlchemySupplierRepository | None = None
        self.stock_movements: SqlAlchemyStockMovementRepository | None = None

    def __enter__(self) -> SqlAlchemyCatalogUnitOfWork:
        self._session = self._session_factory()
        self.products = SqlAlchemyProductRepository(self._session)
        self.categories = SqlAlchemyCategoryRepository(self._session)
        self.suppliers = SqlAlchemySupplierRepository(self._session)
        self.stock_movements = SqlAlchemyStockMovementRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        if self._session is not None:
            self._session.close()

    def commit(self) -> None:
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
