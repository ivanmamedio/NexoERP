"""Application services facade for Credit Notebook."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.credit_notebook.application.apply_payment import (
    ApplyPayment,
    ApplyPaymentInput,
)
from erp.modules.credit_notebook.application.create_customer import (
    CreateCreditCustomer,
    CreateCreditCustomerInput,
    CreateCreditCustomerOutput,
)
from erp.modules.credit_notebook.application.create_entry import (
    CreateCreditEntry,
    CreateCreditEntryInput,
    CreateCreditEntryOutput,
)
from erp.modules.credit_notebook.application.list_customers import (
    ListCreditCustomers,
    ListCreditCustomersInput,
    ListCreditCustomersOutput,
)
from erp.modules.credit_notebook.application.list_entries import (
    ListCreditEntries,
    ListCreditEntriesInput,
    ListCreditEntriesOutput,
)
from erp.modules.credit_notebook.application.update_customer import (
    UpdateCreditCustomer,
    UpdateCreditCustomerInput,
    UpdateCreditCustomerOutput,
)
from erp.modules.credit_notebook.infrastructure.unit_of_work import (
    SqlAlchemyCreditNotebookUnitOfWork,
)


class CreditNotebookServices:
    """Facade de casos de uso do Caderno de Fiado."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # Customer CRUD
    def create_customer(self, input_data: CreateCreditCustomerInput) -> CreateCreditCustomerOutput:
        with SqlAlchemyCreditNotebookUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            result = CreateCreditCustomer(uow.customers).execute(input_data)
            uow.commit()
            return result

    def update_customer(self, input_data: UpdateCreditCustomerInput) -> UpdateCreditCustomerOutput:
        with SqlAlchemyCreditNotebookUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            result = UpdateCreditCustomer(uow.customers).execute(input_data)
            uow.commit()
            return result

    def list_customers(
        self, *, company_id: int | None = None, status: str | None = None, search_query: str = ""
    ) -> ListCreditCustomersOutput:
        with SqlAlchemyCreditNotebookUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            result = ListCreditCustomers(uow.customers).execute(
                ListCreditCustomersInput(
                    company_id=company_id, status=status, search_query=search_query
                )
            )
            uow.commit()
            return result

    # Entry CRUD
    def create_entry(self, input_data: CreateCreditEntryInput) -> CreateCreditEntryOutput:
        with SqlAlchemyCreditNotebookUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            assert uow.entries is not None
            result = CreateCreditEntry(uow.customers, uow.entries).execute(input_data)
            uow.commit()
            return result

    def apply_payment(self, input_data: ApplyPaymentInput) -> None:
        with SqlAlchemyCreditNotebookUnitOfWork(self._engine) as uow:
            assert uow.entries is not None
            ApplyPayment(uow.entries).execute(input_data)
            uow.commit()

    def list_entries(
        self,
        *,
        customer_id: int | None = None,
        company_id: int | None = None,
        status: str | None = None,
        entry_type: str | None = None,
    ) -> ListCreditEntriesOutput:
        with SqlAlchemyCreditNotebookUnitOfWork(self._engine) as uow:
            assert uow.entries is not None
            result = ListCreditEntries(uow.entries).execute(
                ListCreditEntriesInput(
                    customer_id=customer_id,
                    company_id=company_id,
                    status=status,
                    entry_type=entry_type,
                )
            )
            uow.commit()
            return result
