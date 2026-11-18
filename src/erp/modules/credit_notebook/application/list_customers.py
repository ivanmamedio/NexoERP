"""List credit customers use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.credit_notebook.application.ports import CreditCustomerRepository
from erp.modules.credit_notebook.domain.credit_customer import CreditCustomer


@dataclass(slots=True, frozen=True)
class ListCreditCustomersInput:
    company_id: int | None = None
    status: str | None = None
    search_query: str = ""


@dataclass(slots=True, frozen=True)
class CreditCustomerView:
    customer_id: int
    name: str
    phone: str
    email: str
    address: str
    credit_limit_cents: int
    current_balance_cents: int
    available_credit_cents: int
    status: str
    is_over_limit: bool
    total_entries: int


@dataclass(slots=True, frozen=True)
class ListCreditCustomersOutput:
    customers: tuple[CreditCustomerView, ...]


class ListCreditCustomers:
    def __init__(self, repository: CreditCustomerRepository) -> None:
        self._repository = repository

    def execute(self, input_data: ListCreditCustomersInput) -> ListCreditCustomersOutput:
        if input_data.search_query:
            customers = self._repository.search(
                input_data.search_query, input_data.company_id
            )
        else:
            customers = self._repository.list_all(
                input_data.company_id, input_data.status
            )

        views = tuple(
            CreditCustomerView(
                customer_id=c.id or 0,
                name=c.name,
                phone=c.phone,
                email=c.email,
                address=c.address,
                credit_limit_cents=c.credit_limit_cents,
                current_balance_cents=c.current_balance_cents,
                available_credit_cents=c.available_credit_cents,
                status=c.status,
                is_over_limit=c.is_over_limit,
                total_entries=len(c._entries) if c._entries else 0,
            )
            for c in customers
        )
        return ListCreditCustomersOutput(customers=views)