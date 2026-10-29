"""Integration tests for customers repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.customers.domain.customer import Customer
from erp.modules.customers.infrastructure.models import (
    Base,
)
from erp.modules.customers.infrastructure.repository import (
    SqlAlchemyCustomerRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_customer_crud(session: Session) -> None:
    repo = SqlAlchemyCustomerRepository(session)

    customer = Customer(
        company_id=1,
        name="João Silva",
        phone="11999999999",
        document="123.456.789-00",
        credit_limit_cents=50000,
    )
    repo.add(customer)
    assert customer.id is not None

    saved = repo.get_by_id(customer.id or 0)
    assert saved is not None
    assert saved.name == "João Silva"

    customer.name = "João Silva Atualizado"
    repo.save(customer)

    saved = repo.get_by_id(customer.id or 0)
    assert saved is not None
    assert saved.name == "João Silva Atualizado"

    customers = repo.list_by_company(company_id=1)
    assert len(customers) == 1


def test_customer_isolation_between_companies(session: Session) -> None:
    repo = SqlAlchemyCustomerRepository(session)

    repo.add(Customer(company_id=1, name="Cliente A"))
    repo.add(Customer(company_id=2, name="Cliente B"))

    customers_1 = repo.list_by_company(company_id=1)
    customers_2 = repo.list_by_company(company_id=2)

    assert len(customers_1) == 1
    assert customers_1[0].name == "Cliente A"
    assert len(customers_2) == 1
    assert customers_2[0].name == "Cliente B"

    # Empresa 1 não deve ver cliente da empresa 2
    repo.get_by_phone("11999999999", company_id=1)
    # Como não definimos telefone no teste, só testamos list_by_company
