"""SQLAlchemy Unit of Work for the purchases module."""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.modules.purchases.infrastructure.repository import (
    SqlAlchemyPurchaseItemRepository,
    SqlAlchemyPurchaseRepository,
)
from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemyPurchasesUnitOfWork(UnitOfWork):
    """Unit of Work implementation for purchases using a single session."""

    def __init__(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self.purchases: SqlAlchemyPurchaseRepository | None = None
        self.purchase_items: SqlAlchemyPurchaseItemRepository | None = None

    def __enter__(self) -> SqlAlchemyPurchasesUnitOfWork:
        self._session = self._session_factory()
        self.purchases = SqlAlchemyPurchaseRepository(self._session)
        self.purchase_items = SqlAlchemyPurchaseItemRepository(self._session)
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
