"""Integration tests for Import CSV module using SQLite in-memory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.catalog.infrastructure.models import Base as CatalogBase
from erp.modules.catalog.infrastructure.repository import (
    SqlAlchemyProductRepository,
)
from erp.modules.import_csv.application.import_products_use_case import (
    ImportProductsInput,
    ImportProductsUseCase,
)
from erp.modules.import_csv.application.services import ImportProductsServices
from erp.modules.import_csv.infrastructure.csv_parser import CSVProductParser


def _make_csv(tmp_path: Path, content: str) -> Path:
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(content, encoding="utf-8")
    return csv_file


def test_import_and_verify_in_db(tmp_path: Path) -> None:
    """Testa importação completa: CSV -> banco de dados."""
    engine = create_engine("sqlite:///:memory:")
    CatalogBase.metadata.create_all(engine)
    session = Session(engine)

    product_repo = SqlAlchemyProductRepository(session)

    # Cria CSV com produtos
    csv_content = (
        "sku,name,unit,cost_cents,margin_pct,price_cents,min_stock_qty,"
        "stock_qty,sold_by_weight,active,category_name,supplier_name\n"
        "ARROZ-5KG,Arroz 5kg,un,5000,3000,6500,1000,50000,false,true,"
        "Cereais,Fornecedor A\n"
        "FEIJAO-1KG,Feijão 1kg,un,3000,4000,4200,500,20000,false,true,"
        "Cereais,Fornecedor B"
    )
    csv_file = _make_csv(tmp_path, csv_content)

    use_case = ImportProductsUseCase(
        product_repo=product_repo,
        result_repo=None,  # type: ignore[arg-type]
        user_permissions={"product.import"},
    )

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    session.commit()  # Confirma a transação

    assert output.result.imported_count == 2
    assert output.result.error_count == 0

    # Verifica no banco

    arroz = product_repo.get_by_sku("ARROZ-5KG", company_id=1)
    assert arroz is not None
    assert arroz.name == "Arroz 5kg"
    assert arroz.price_cents == 6500
    assert arroz.company_id == 1

    feijao = product_repo.get_by_sku("FEIJAO-1KG", company_id=1)
    assert feijao is not None
    assert feijao.name == "Feijão 1kg"
    assert feijao.price_cents == 4200


def test_import_isolation_between_companies(tmp_path: Path) -> None:
    """Produtos importados para empresa 1 não devem aparecer na empresa 2."""
    engine = create_engine("sqlite:///:memory:")
    CatalogBase.metadata.create_all(engine)
    session = Session(engine)

    product_repo = SqlAlchemyProductRepository(session)

    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,6500"""
    csv_file = _make_csv(tmp_path, csv_content)

    use_case = ImportProductsUseCase(
        product_repo=product_repo,
        result_repo=None,  # type: ignore[arg-type]
        user_permissions={"product.import"},
    )

    # Importa para empresa 1
    output1 = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )
    session.commit()
    assert output1.result.imported_count == 1

    # Empresa 2 não deve ver o produto
    arroz = product_repo.get_by_sku("ARROZ-5KG", company_id=2)
    assert arroz is None

    # Empresa 1 deve ver
    arroz = product_repo.get_by_sku("ARROZ-5KG", company_id=1)
    assert arroz is not None


def test_csv_parser_parses_headers(tmp_path: Path) -> None:
    """Testa o parser de CSV."""
    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,6500
FEIJAO-1KG,Feijão 1kg,4200"""
    csv_file = _make_csv(tmp_path, csv_content)

    parser = CSVProductParser()
    rows = parser.parse(str(csv_file), encoding="utf-8")

    assert len(rows) == 2
    assert rows[0]["sku"] == "ARROZ-5KG"
    assert rows[0]["name"] == "Arroz 5kg"
    assert rows[0]["price_cents"] == "6500"


def test_csv_parser_validates_headers(tmp_path: Path) -> None:
    """Testa validação de cabeçalhos obrigatórios."""
    csv_content = """nome,preco
Arroz 5kg,6500"""
    csv_file = _make_csv(tmp_path, csv_content)

    parser = CSVProductParser()
    rows = parser.parse(str(csv_file), encoding="utf-8")

    errors = parser.validate_headers(list(rows[0].keys()) if rows else [])
    # Como não tem 'sku' nem 'name' (tem 'nome'), deve haver erro
    assert len(errors) > 0
    assert any("sku" in e.message.lower() for e in errors)


def test_import_services_facade(tmp_path: Path) -> None:
    """Testa a fachada de serviços."""
    engine = create_engine("sqlite:///:memory:")
    CatalogBase.metadata.create_all(engine)
    session = Session(engine)

    product_repo = SqlAlchemyProductRepository(session)

    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,6500"""
    csv_file = _make_csv(tmp_path, csv_content)

    services = ImportProductsServices(
        product_repo=product_repo,
        result_repo=None,  # type: ignore[arg-type]
        user_permissions={"product.import"},
    )

    output = services.import_csv(
        file_path=str(csv_file),
        company_id=1,
        user_id=1,
        username="gerente",
    )
    session.commit()

    assert output.result.imported_count == 1


def test_import_skips_invalid_lines(tmp_path: Path) -> None:
    """Testa pular linhas inválidas."""
    engine = create_engine("sqlite:///:memory:")
    CatalogBase.metadata.create_all(engine)
    session = Session(engine)

    product_repo = SqlAlchemyProductRepository(session)

    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,6500
,Produto sem SKU,7000
FEIJAO-1KG,Feijão 1kg,abc"""
    csv_file = _make_csv(tmp_path, csv_content)

    use_case = ImportProductsUseCase(
        product_repo=product_repo,
        result_repo=None,  # type: ignore[arg-type]
        user_permissions={"product.import"},
    )

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
            skip_invalid=True,
        )
    )
    session.commit()

    assert output.result.imported_count == 1
    assert output.result.error_count == 2


def test_import_encoding_latin1(tmp_path: Path) -> None:
    """Testa importação com codificação Latin-1."""
    engine = create_engine("sqlite:///:memory:")
    CatalogBase.metadata.create_all(engine)
    session = Session(engine)

    product_repo = SqlAlchemyProductRepository(session)

    csv_content = "sku,name,price_cents\nARROZ-5KG,Arroz 5kg,6500"
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="latin-1")

    use_case = ImportProductsUseCase(
        product_repo=product_repo,
        result_repo=None,  # type: ignore[arg-type]
        user_permissions={"product.import"},
    )

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
            encoding="latin-1",
        )
    )
    session.commit()

    assert output.result.imported_count == 1
