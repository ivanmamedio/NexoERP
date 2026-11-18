"""SQLAlchemy Unit of Work for Credit Notebook."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from erp.modules.credit_notebook.application.ports import (
    CreditCustomerRepository,
    CreditEntryRepository,
)
from erp.modules.credit_notebook.infrastructure.repository import (
    SqlAlchemyCreditCustomerRepository,
    SqlAlchemyCreditEntryRepository,
)
from erp.shared.infrastructure.uow import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class SqlAlchemyCreditNotebookUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """Unit of work for Credit Notebook module."""

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.customers: CreditCustomerRepository | None = None
        self.entries: CreditEntryRepository | None = None

    def _create_session(self) -> Session:
        session = super()._create_session()
        self.customers = SqlAlchemyCreditCustomerRepository(session)
        self.entries = SqlAlchemyCreditEntryRepository(session)
        return session


# Factory function for dependency inversion
def credit_notebook_uow_factory(engine: Engine) -> Callable[[], SqlAlchemyCreditNotebookUnitOfWork]:
    return lambda: SqlAlchemyCreditNotebookUnitOfWork(engine)