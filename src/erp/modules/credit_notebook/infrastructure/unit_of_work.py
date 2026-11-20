"""SQLAlchemy Unit of Work for Credit Notebook."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from sqlalchemy.orm import Session

from erp.modules.credit_notebook.application.ports import (
    CreditCustomerRepository,
    CreditEntryRepository,
)
from erp.modules.credit_notebook.infrastructure.repository import (
    SqlAlchemyCreditCustomerRepository,
    SqlAlchemyCreditEntryRepository,
)
from erp.shared.infrastructure.unit_of_work_base import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class SqlAlchemyCreditNotebookUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """Unit of work for Credit Notebook module."""

    customers: CreditCustomerRepository | None = None
    entries: CreditEntryRepository | None = None

    def __init__(self, engine: Engine) -> None:
        super().__init__(
            engine,
            repo_factories={
                "customers": SqlAlchemyCreditCustomerRepository,
                "entries": SqlAlchemyCreditEntryRepository,
            },
        )

    def __enter__(self) -> SqlAlchemyCreditNotebookUnitOfWork:
        return cast(SqlAlchemyCreditNotebookUnitOfWork, super().__enter__())

    @property
    def session(self) -> Session:
        return super().session


# Factory function for dependency inversion
def credit_notebook_uow_factory(engine: Engine) -> Callable[[], SqlAlchemyCreditNotebookUnitOfWork]:
    return lambda: SqlAlchemyCreditNotebookUnitOfWork(engine)
