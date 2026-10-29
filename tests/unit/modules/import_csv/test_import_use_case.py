"""Unit tests for ImportProductsUseCase."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from erp.modules.import_csv.application.import_products_use_case import (
    ImportProductsInput,
    ImportProductsUseCase,
)
from erp.modules.import_csv.domain.import_result import (
    ImportResult,
)
from erp.shared.domain.errors import PermissionDenied, ValidationError


class FakeProductCatalogPort:
    def __init__(self) -> None:
        self.existing_skus: set[str] = set()

    def get_by_sku(self, sku: str, company_id: int | None = None) -> object | None:
        return None

    def list_all_skus(self, company_id: int | None = None) -> list[str]:
        return list(self.existing_skus)

    def add(self, product: object) -> None:
        self.existing_skus.add(product.sku)

    def add_snapshot(self, product: object) -> None:
        self.existing_skus.add(product.sku)

    def commit(self) -> None:
        pass


class FakeImportResultRepositoryPort:
    def __init__(self) -> None:
        self.saved_results: list[ImportResult] = []

    def save_result(self, result: ImportResult) -> None:
        self.saved_results.append(result)

    def get_result(self, import_id: int) -> ImportResult | None:
        return None


def _make_input(**kwargs) -> ImportProductsInput:
    defaults: dict = {
        "file_path": "/tmp/test.csv",
        "company_id": 1,
        "user_id": 1,
        "username": "gerente",
        "skip_invalid": False,
        "encoding": "utf-8",
    }
    defaults.update(kwargs)
    return ImportProductsInput(**defaults)


def test_import_requires_permission() -> None:
    """Deve exigir permissão product.import."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, set())

    with pytest.raises(PermissionDenied, match=re.escape("product.import")):
        use_case.execute(_make_input())


def test_import_success(tmp_path: Path) -> None:
    """Deve importar produtos com sucesso."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    # Cria arquivo CSV
    csv_content = (
        "sku,name,unit,cost_cents,margin_pct,price_cents,min_stock_qty,"
        "stock_qty,sold_by_weight,active,category_name,supplier_name\n"
        "ARROZ-5KG,Arroz 5kg,un,5000,3000,6500,1000,50000,false,true,"
        "Cereais,Fornecedor A\n"
        "FEIJAO-1KG,Feijão 1kg,un,3000,4000,4200,500,20000,false,true,"
        "Cereais,Fornecedor B"
    )
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    assert output.result.imported_count == 2
    assert output.result.error_count == 0
    assert len(output.result.imported_products) == 2
    assert output.result.imported_products[0].sku == "ARROZ-5KG"
    assert output.result.imported_products[0].name == "Arroz 5kg"
    assert output.result.imported_products[0].price_cents == 6500


def test_import_duplicate_sku_in_csv(tmp_path: Path) -> None:
    """Não deve importar SKU duplicado dentro do mesmo CSV."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,6500
ARROZ-5KG,Arroz 5kg duplicado,7000"""
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    assert output.result.imported_count == 1
    assert output.result.error_count == 1
    assert "duplicado" in output.result.errors[0].message


def test_import_invalid_price(tmp_path: Path) -> None:
    """Deve rejeitar preço inválido."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,abc"""
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    assert output.result.imported_count == 0
    assert output.result.error_count == 1
    assert "inválido" in output.result.errors[0].message.lower()


def test_import_missing_required_fields(tmp_path: Path) -> None:
    """Deve rejeitar linhas sem SKU ou nome."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    csv_content = """sku,name,price_cents
,Produto sem SKU,1000
ARROZ-5KG,,6500"""
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    assert output.result.imported_count == 0
    assert output.result.error_count == 2


def test_import_pt_br_decimal(tmp_path: Path) -> None:
    """Deve converter vírgula decimal pt-BR para centavos."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    # CSV com vírgula como separador decimal deve ser aspas para não quebrar o CSV
    csv_content = '''sku,name,price_cents
"ARROZ-5KG","Arroz 5kg","16,39"'''
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    assert output.result.imported_count == 1
    assert output.result.imported_products[0].price_cents == 1639


def test_import_existing_sku_in_db(tmp_path: Path) -> None:
    """Não deve importar SKU que já existe no banco."""
    repo = FakeProductCatalogPort()
    repo.existing_skus = {"ARROZ-5KG"}
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    csv_content = """sku,name,price_cents
ARROZ-5KG,Arroz 5kg,6500"""
    csv_file = tmp_path / "produtos.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output = use_case.execute(
        ImportProductsInput(
            file_path=str(csv_file),
            company_id=1,
            user_id=1,
            username="gerente",
        )
    )

    assert output.result.imported_count == 0
    assert output.result.error_count == 1


def test_import_file_not_found() -> None:
    """Deve lançar ValidationError se arquivo não existir."""
    repo = FakeProductCatalogPort()
    result_repo = FakeImportResultRepositoryPort()
    use_case = ImportProductsUseCase(repo, result_repo, {"product.import"})

    with pytest.raises(ValidationError, match="não encontrado"):
        use_case.execute(
            ImportProductsInput(
                file_path="/tmp/nao_existe.csv",
                company_id=1,
                user_id=1,
                username="gerente",
            )
        )


def test_import_result_success_rate() -> None:
    """Testa cálculo de taxa de sucesso."""
    result = ImportResult(
        total_lines=10,
        imported_count=8,
        error_count=2,
    )
    assert result.success_rate == 80.0


def test_import_result_no_lines() -> None:
    """Testa taxa de sucesso com zero linhas."""
    result = ImportResult()
    assert result.success_rate == 100.0
