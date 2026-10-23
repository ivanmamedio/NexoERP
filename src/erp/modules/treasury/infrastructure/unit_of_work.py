"""SQLAlchemy Unit of Work for the treasury module."""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.modules.treasury.infrastructure.repository import (
    SqlAlchemyFinancialCategoryRepository,
    SqlAlchemyFinancialEntryRepository,
    SqlAlchemyPayableRepository,
    SqlAlchemyReceivableRepository,
)
from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemyTreasuryUnitOfWork(UnitOfWork):
    """Unit of Work implementation for treasury using a single session."""

    def __init__(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self.financial_entries: SqlAlchemyFinancialEntryRepository | None = None
        self.financial_categories: SqlAlchemyFinancialCategoryRepository | None = None
        self.payables: SqlAlchemyPayableRepository | None = None
        self.receivables: SqlAlchemyReceivableRepository | None = None

    def __enter__(self) -> SqlAlchemyTreasuryUnitOfWork:
        self._session = self._session_factory()
        self.financial_entries = SqlAlchemyFinancialEntryRepository(self._session)
        self.financial_categories = SqlAlchemyFinancialCategoryRepository(self._session)
        self.payables = SqlAlchemyPayableRepository(self._session)
        self.receivables = SqlAlchemyReceivableRepository(self._session)
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
