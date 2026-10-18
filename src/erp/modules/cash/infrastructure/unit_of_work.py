"""SQLAlchemy Unit of Work for the cash module."""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.modules.cash.infrastructure.repository import (
    SqlAlchemyCashMovementRepository,
    SqlAlchemyCashRegisterRepository,
    SqlAlchemyCashSessionRepository,
)
from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemyCashUnitOfWork(UnitOfWork):
    """Unit of Work implementation for cash using a single session."""

    def __init__(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self.registers: SqlAlchemyCashRegisterRepository | None = None
        self.sessions: SqlAlchemyCashSessionRepository | None = None
        self.movements: SqlAlchemyCashMovementRepository | None = None

    def __enter__(self) -> SqlAlchemyCashUnitOfWork:
        self._session = self._session_factory()
        self.registers = SqlAlchemyCashRegisterRepository(self._session)
        self.sessions = SqlAlchemyCashSessionRepository(self._session)
        self.movements = SqlAlchemyCashMovementRepository(self._session)
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
