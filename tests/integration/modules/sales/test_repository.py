"""Integration tests for sales repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.modules.sales.domain.sale_payment import SalePayment
from erp.modules.sales.infrastructure.models import (
    Base,
)
from erp.modules.sales.infrastructure.repository import (
    SqlAlchemySaleItemRepository,
    SqlAlchemySalePaymentRepository,
    SqlAlchemySaleRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_sale_crud(session: Session) -> None:
    repo = SqlAlchemySaleRepository(session)
    item_repo = SqlAlchemySaleItemRepository(session)
    pay_repo = SqlAlchemySalePaymentRepository(session)

    sale = Sale(user_id=1, username="caixa", company_id=1)
    repo.add(sale)
    assert sale.id is not None

    item = SaleItem(
        sale_id=sale.id or 0,
        company_id=1,
        product_id=1,
        description="Arroz 5kg",
        unit_price_cents=2500,
        quantity_thousandths=2000,
        line_total_cents=5000,
    )
    item_repo.add(item)
    assert item.id is not None

    payment = SalePayment(sale_id=sale.id or 0, company_id=1, method="cash", amount_cents=5000)
    pay_repo.add(payment)
    assert payment.id is not None

    sale.finalize(paid_cents=5000, change_cents=0)
    repo.save(sale)

    saved = repo.get_by_id(sale.id or 0)
    assert saved is not None
    assert saved.is_finalized()

    items = item_repo.list_by_sale(sale.id or 0)
    assert len(items) == 1

    payments = pay_repo.list_by_sale(sale.id or 0)
    assert len(payments) == 1


def test_sale_list_open_filters_by_company(session: Session) -> None:
    """list_open deve retornar apenas vendas da empresa informada."""
    repo = SqlAlchemySaleRepository(session)

    sale_a = Sale(user_id=1, username="caixa", company_id=1)
    sale_b = Sale(user_id=2, username="caixa", company_id=2)
    repo.add(sale_a)
    repo.add(sale_b)

    empresas_1 = repo.list_open(company_id=1)
    empresas_2 = repo.list_open(company_id=2)

    assert len(empresas_1) == 1
    assert empresas_1[0].company_id == 1
    assert len(empresas_2) == 1
    assert empresas_2[0].company_id == 2


def test_sale_get_by_id_isolates_companies(session: Session) -> None:
    """Uma empresa não deve acessar vendas de outra empresa via get_by_id."""
    repo = SqlAlchemySaleRepository(session)

    sale_a = Sale(user_id=1, username="caixa", company_id=1)
    sale_b = Sale(user_id=2, username="caixa", company_id=2)
    repo.add(sale_a)
    repo.add(sale_b)

    # Empresa 1 não deve ver a venda da empresa 2
    found = repo.get_by_id(sale_b.id or 0, company_id=1)
    assert found is None, "Empresa 1 não deveria acessar venda da empresa 2"

    # Empresa 2 não deve ver a venda da empresa 1
    found = repo.get_by_id(sale_a.id or 0, company_id=2)
    assert found is None, "Empresa 2 não deveria acessar venda da empresa 1"
