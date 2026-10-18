"""SQLAlchemy Unit of Work for the sales module."""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.modules.sales.infrastructure.repository import (
    SqlAlchemySaleItemRepository,
    SqlAlchemySalePaymentRepository,
    SqlAlchemySaleRepository,
)
from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemySalesUnitOfWork(UnitOfWork):
    """Unit of Work implementation for sales using a single session."""

    def __init__(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self.sales: SqlAlchemySaleRepository | None = None
        self.items: SqlAlchemySaleItemRepository | None = None
        self.payments: SqlAlchemySalePaymentRepository | None = None

    def __enter__(self) -> SqlAlchemySalesUnitOfWork:
        self._session = self._session_factory()
        self.sales = SqlAlchemySaleRepository(self._session)
        self.items = SqlAlchemySaleItemRepository(self._session)
        self.payments = SqlAlchemySalePaymentRepository(self._session)
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
