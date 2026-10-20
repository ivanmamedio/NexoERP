"""Integration tests for catalog repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from erp.modules.catalog.domain.category import Category
from erp.modules.catalog.domain.product import Product
from erp.modules.catalog.domain.supplier import Supplier
from erp.modules.catalog.infrastructure.models import (
    Base,
)
from erp.modules.catalog.infrastructure.repository import (
    SqlAlchemyCategoryRepository,
    SqlAlchemyProductRepository,
    SqlAlchemySupplierRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_product_crud(session: Session) -> None:
    repo = SqlAlchemyProductRepository(session)

    product = Product(
        sku="P001",
        name="Arroz 5kg",
        unit="un",
        cost_cents=1000,
        price_cents=1300,
        stock_qty=50000,
        company_id=1,
    )
    repo.add(product)

    saved = repo.get_by_id(product.id)
    assert saved is not None
    assert saved.sku == "P001"
    assert saved.name == "Arroz 5kg"
    assert saved.company_id == 1

    by_sku = repo.get_by_sku("P001")
    assert by_sku is not None
    assert by_sku.id == product.id

    products = repo.list_all()
    assert len(products) == 1


def test_product_company_isolation(session: Session) -> None:
    repo = SqlAlchemyProductRepository(session)

    p1 = Product(sku="P001", name="Produto A", company_id=1, stock_qty=10000)
    p2 = Product(sku="P002", name="Produto B", company_id=2, stock_qty=20000)
    repo.add(p1)
    repo.add(p2)

    # Sem company_id na sessão, filtra por nada (não há CurrentSession.company_id)
    # Cada chamada de list_all filtra pela sessão atual. Como não há sessão ativa,
    # não filtra por company_id. Para testar isolamento, usamos company_id explícito.
    all_p1 = repo.list_all(company_id=1)
    all_p2 = repo.list_all(company_id=2)
    assert len(all_p1) == 1
    assert all_p1[0].name == "Produto A"
    assert len(all_p2) == 1
    assert all_p2[0].name == "Produto B"


def test_product_search_by_name_is_company_scoped_and_ignores_inactive(
    session: Session,
) -> None:
    repo = SqlAlchemyProductRepository(session)
    repo.add(Product(sku="A1", name="Arroz 5kg", company_id=1))
    repo.add(Product(sku="A2", name="Arroz 1kg", company_id=1))
    repo.add(Product(sku="A3", name="Arroz inativo", company_id=1, active=False))
    repo.add(Product(sku="A4", name="Arroz 2kg", company_id=2))
    repo.add(Product(sku="F1", name="Feijão carioca", company_id=1))

    company_1 = repo.search("arr", company_id=1)
    assert [p.sku for p in company_1] == ["A2", "A1"]  # ordenado por nome
    assert all(p.company_id == 1 for p in company_1)

    assert [p.sku for p in repo.search("arr", company_id=2)] == ["A4"]
    # Busca é case-insensitive (índice NOCASE).
    assert [p.sku for p in repo.search("ARROZ", company_id=1)] == ["A2", "A1"]

    # Sem prefixo correspondente, cai para substring.
    assert [p.sku for p in repo.search("carioca", company_id=1)] == ["F1"]
    # Wildcards são escapados (não viram busca ampla).
    assert repo.search("%", company_id=1) == []


def test_product_search_uses_composite_nocase_index(session: Session) -> None:
    plan = " ".join(
        str(row)
        for row in session.execute(
            text(
                "EXPLAIN QUERY PLAN "
                "SELECT id FROM products "
                "WHERE company_id = 1 AND name LIKE 'arr%'"
            )
        ).all()
    )
    assert "ix_products_company_name_nocase" in plan


def test_supplier_and_category_crud(session: Session) -> None:
    cat_repo = SqlAlchemyCategoryRepository(session)
    sup_repo = SqlAlchemySupplierRepository(session)

    category = Category(name="Mercearia", company_id=1)
    cat_repo.add(category)
    assert category.id is not None

    supplier = Supplier(name="Fornecedor X", tax_id="12345678000190", company_id=1)
    sup_repo.add(supplier)
    assert supplier.id is not None

    cats = cat_repo.list_all(company_id=1)
    assert len(cats) == 1
    assert cats[0].name == "Mercearia"

    sups = sup_repo.list_all(company_id=1)
    assert len(sups) == 1
    assert sups[0].tax_id == "12345678000190"
