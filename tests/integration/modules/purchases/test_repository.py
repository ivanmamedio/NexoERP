"""Integration tests for purchases repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.purchases.domain.purchase import Purchase
from erp.modules.purchases.infrastructure.models import (
    Base,
)
from erp.modules.purchases.infrastructure.repository import (
    SqlAlchemyPurchaseRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_purchase_crud(session: Session) -> None:
    repo = SqlAlchemyPurchaseRepository(session)

    purchase = Purchase(
        company_id=1,
        supplier_id=1,
        user_id=1,
        username="gerente",
        total_cents=5000,
    )
    repo.add(purchase)
    assert purchase.id is not None

    saved = repo.get_by_id(purchase.id or 0)
    assert saved is not None
    assert saved.total_cents == 5000
    assert saved.status == "registered"


def test_purchase_list_by_company_isolation(session: Session) -> None:
    repo = SqlAlchemyPurchaseRepository(session)

    purchase_a = Purchase(company_id=1, total_cents=1000)
    purchase_b = Purchase(company_id=2, total_cents=2000)
    repo.add(purchase_a)
    repo.add(purchase_b)

    companies_1 = repo.list_by_company(company_id=1)
    companies_2 = repo.list_by_company(company_id=2)

    assert len(companies_1) == 1
    assert companies_1[0].total_cents == 1000
    assert len(companies_2) == 1
    assert companies_2[0].total_cents == 2000
