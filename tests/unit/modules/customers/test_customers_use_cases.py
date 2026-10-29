"""Unit tests for Customers use cases."""

from __future__ import annotations

import re

import pytest

from erp.modules.customers.application.create_customer import (
    CreateCustomer,
    CreateCustomerInput,
)
from erp.modules.customers.application.find_customers import (
    FindCustomers,
    FindCustomersInput,
)
from erp.modules.customers.application.update_customer import (
    UpdateCustomer,
    UpdateCustomerInput,
)
from erp.modules.customers.domain.customer import Customer
from erp.shared.domain.errors import PermissionDenied, ValidationError


class FakeCustomerRepository:
    def __init__(self) -> None:
        self._customers: dict[int, Customer] = {}
        self._next_id = 1

    def add(self, customer: Customer) -> None:
        customer.id = self._next_id
        self._next_id += 1
        self._customers[customer.id] = customer

    def save(self, customer: Customer) -> None:
        self._customers[customer.id] = customer

    def get_by_id(self, customer_id: int) -> Customer | None:
        return self._customers.get(customer_id)

    def get_by_phone(self, phone: str, company_id: int) -> Customer | None:
        for c in self._customers.values():
            if c.phone == phone and c.company_id == company_id:
                return c
        return None

    def list_by_company(self, company_id: int, name_contains: str | None = None) -> list[Customer]:
        result = [c for c in self._customers.values() if c.company_id == company_id]
        if name_contains:
            result = [c for c in result if name_contains.lower() in c.name.lower()]
        return result


def _make_customer_input(**kwargs) -> CreateCustomerInput:
    defaults: dict[str, object] = {
        "name": "João Silva",
        "phone": "11999999999",
        "company_id": 1,
        "user_id": 1,
        "username": "gerente",
    }
    defaults.update(kwargs)
    return CreateCustomerInput(**defaults)


def test_create_customer_requires_permission() -> None:
    repo = FakeCustomerRepository()

    with pytest.raises(PermissionDenied, match=re.escape("customer.create")):
        CreateCustomer(repo, set()).execute(_make_customer_input())


def test_create_customer_success() -> None:
    repo = FakeCustomerRepository()

    output = CreateCustomer(repo, {"customer.create"}).execute(_make_customer_input())
    assert output.customer_id == 1
    assert output.name == "João Silva"

    saved = repo.get_by_id(1)
    assert saved is not None
    assert saved.name == "João Silva"
    assert saved.company_id == 1


def test_create_customer_requires_name() -> None:
    repo = FakeCustomerRepository()

    with pytest.raises(ValidationError, match="obrigatório"):
        CreateCustomer(repo, {"customer.create"}).execute(
            CreateCustomerInput(name="", company_id=1, user_id=1, username="gerente")
        )


def test_create_customer_isolation_between_companies() -> None:
    repo = FakeCustomerRepository()

    CreateCustomer(repo, {"customer.create"}).execute(
        CreateCustomerInput(name="Cliente A", company_id=1, user_id=1, username="gerente")
    )
    CreateCustomer(repo, {"customer.create"}).execute(
        CreateCustomerInput(name="Cliente B", company_id=2, user_id=1, username="gerente")
    )

    customers_1 = repo.list_by_company(company_id=1)
    customers_2 = repo.list_by_company(company_id=2)
    assert len(customers_1) == 1
    assert len(customers_2) == 1
    assert customers_1[0].name == "Cliente A"
    assert customers_2[0].name == "Cliente B"


def test_update_customer_requires_permission() -> None:
    repo = FakeCustomerRepository()
    repo.add(Customer(company_id=1, name="João", id=1))

    with pytest.raises(PermissionDenied, match=re.escape("customer.update")):
        UpdateCustomer(repo, set()).execute(
            UpdateCustomerInput(customer_id=1, name="João Atualizado", company_id=1)
        )


def test_update_customer_isolation_between_companies() -> None:
    repo = FakeCustomerRepository()
    repo.add(Customer(company_id=1, name="João", id=1))

    with pytest.raises(PermissionDenied, match="pertence à empresa"):
        UpdateCustomer(repo, {"customer.update"}).execute(
            UpdateCustomerInput(customer_id=1, name="João Atualizado", company_id=2)
        )


def test_find_customers_requires_permission() -> None:
    repo = FakeCustomerRepository()

    with pytest.raises(PermissionDenied, match=re.escape("customer.read")):
        FindCustomers(repo, set()).execute(FindCustomersInput(company_id=1))


def test_find_customers_by_name() -> None:
    repo = FakeCustomerRepository()
    repo.add(Customer(company_id=1, name="João Silva", id=1))
    repo.add(Customer(company_id=1, name="Maria Souza", id=2))
    repo.add(Customer(company_id=2, name="João Silva", id=3))

    result = FindCustomers(repo, {"customer.read"}).execute(
        FindCustomersInput(company_id=1, name_contains="joão")
    )
    assert len(result) == 1
    assert result[0].name == "João Silva"
    assert result[0].customer_id == 1
