"""Base SQLAlchemy Unit of Work class.

Eliminates boilerplate in module-specific UnitOfWork implementations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from erp.shared.application.ports import UnitOfWork
from erp.shared.infrastructure.database import get_session_factory


class SqlAlchemyUnitOfWorkBase(UnitOfWork):
    """Base Unit of Work that manages repositories via factory functions.

    Subclasses define `repo_factories` dict mapping attribute names to
    callables that create repository instances from a Session.
    """

    # Common repository attributes (set in __enter__)
    users: Any = None
    roles: Any = None
    permissions: Any = None
    companies: Any = None
    products: Any = None
    categories: Any = None
    suppliers: Any = None
    stock_movements: Any = None
    sales: Any = None
    items: Any = None
    payments: Any = None
    cash_sessions: Any = None
    movements: Any = None
    financial_entries: Any = None
    audit_logs: Any = None

    def __init__(
        self,
        engine: Engine,
        repo_factories: dict[str, Callable[[Session], Any]] | None = None,
    ) -> None:
        if not isinstance(engine, Engine):
            raise TypeError("engine must be a SQLAlchemy Engine instance")
        self._engine: Engine = engine
        self._session_factory = get_session_factory(engine)
        self._session: Session | None = None
        self._repo_factories = repo_factories or {}
        # Repositories will be created on __enter__
        for name in self._repo_factories:
            setattr(self, name, None)

    def __enter__(self) -> SqlAlchemyUnitOfWorkBase:
        self._session = self._session_factory()
        for name, factory in self._repo_factories.items():
            setattr(self, name, factory(self._session))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        if self._session is not None:
            self._session.close()
            self._session = None
        # Clear repositories
        for name in self._repo_factories:
            setattr(self, name, None)

    def commit(self) -> None:
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()

    @property
    def session(self) -> Session:
        if not self._session:
            raise RuntimeError("UnitOfWork not entered")
        return self._session