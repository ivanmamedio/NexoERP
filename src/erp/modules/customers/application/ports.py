"""Application ports for the customers module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.customers.domain.customer import Customer


@runtime_checkable
class CustomerRepository(Protocol):
    """Repository port for Customer aggregates."""

    def add(self, customer: Customer) -> None: ...
    def save(self, customer: Customer) -> None: ...
    def get_by_id(self, customer_id: int) -> Customer | None: ...
    def get_by_phone(self, phone: str, company_id: int) -> Customer | None: ...
    def list_by_company(
        self, company_id: int, name_contains: str | None = None
    ) -> list[Customer]: ...
