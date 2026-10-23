"""Import products from CSV use case."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from typing import TYPE_CHECKING

from erp.modules.import_csv.application.ports import (
    ImportResultRepositoryPort,
    ProductCatalogPort,
)
from erp.modules.import_csv.domain.import_result import (
    ImportedProduct,
    ImportError,
    ImportResult,
)
from erp.shared.domain.errors import PermissionDenied, ValidationError

if TYPE_CHECKING:
    pass


@dataclass(slots=True, frozen=True)
class ImportProductsInput:
    """Entrada para importação de produtos por CSV."""

    file_path: str
    company_id: int
    user_id: int | None
    username: str
    skip_invalid: bool = False
    encoding: str = "utf-8"


@dataclass(slots=True, frozen=True)
class ImportProductsOutput:
    """Saída da importação de produtos."""

    result: ImportResult


class ImportProductsUseCase:
    """Importa produtos de um arquivo CSV.

    Valida cada linha, converte preços para centavos (Decimal, nunca float),
    verifica SKUs duplicados e aplica em uma única transação.
    """

    def __init__(
        self,
        product_repo: ProductCatalogPort,
        result_repo: ImportResultRepositoryPort,
        user_permissions: set[str],
    ) -> None:
        self._product_repo = product_repo
        self._result_repo = result_repo
        self._user_permissions = user_permissions

    def execute(self, input: ImportProductsInput) -> ImportProductsOutput:
        """Executa a importação de produtos CSV."""

        if "product.import" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para importar produtos (product.import)."
            )

        result = ImportResult()

        try:
            with open(input.file_path, encoding=input.encoding, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            result.total_lines = len(rows)

            existing_skus = set(self._product_repo.list_all_skus(input.company_id))
            seen_skus: set[str] = set()

            for line_number, row in enumerate(rows, start=2):  # header é linha 1
                self._process_row(
                    row,
                    line_number,
                    input.company_id,
                    existing_skus,
                    seen_skus,
                    result,
                )

            # Aplica em uma única transação
            self._product_repo.commit()
            if self._result_repo is not None:
                self._result_repo.save_result(result)

        except FileNotFoundError as exc:
            raise ValidationError(f"Arquivo não encontrado: {input.file_path}") from exc
        except UnicodeDecodeError as exc:
            raise ValidationError(
                f"Erro de codificação: {exc}. Tente especificar a codificação correta."
            ) from exc
        except Exception as exc:
            raise ValidationError(f"Erro ao importar CSV: {exc}") from exc

        return ImportProductsOutput(result=result)

    def _process_row(
        self,
        row: dict[str, str],
        line_number: int,
        company_id: int,
        existing_skus: set[str],
        seen_skus: set[str],
        result: ImportResult,
    ) -> None:
        """Processa uma linha do CSV."""

        sku = (row.get("sku") or "").strip().upper()
        name = (row.get("name") or "").strip()

        # Validações básicas
        if not sku:
            result.errors.append(
                ImportError(
                    line_number=line_number,
                    field="sku",
                    message="SKU é obrigatório.",
                    value=row.get("sku", ""),
                )
            )
            result.error_count += 1
            return

        if not name:
            result.errors.append(
                ImportError(
                    line_number=line_number,
                    field="name",
                    message="Nome do produto é obrigatório.",
                    value=row.get("name", ""),
                )
            )
            result.error_count += 1
            return

        # Verifica duplicidade (já existente no banco ou no próprio CSV)
        if sku in existing_skus or sku in seen_skus:
            result.errors.append(
                ImportError(
                    line_number=line_number,
                    field="sku",
                    message=f"SKU duplicado: {sku}",
                    value=sku,
                )
            )
            result.error_count += 1
            return

        seen_skus.add(sku)

        # Converte preços para centavos (Decimal, nunca float)
        cost_cents = self._parse_money(
            row.get("cost_cents", "0"), line_number, "cost_cents", result
        )
        if cost_cents is None:
            return

        price_cents = self._parse_money(
            row.get("price_cents", "0"), line_number, "price_cents", result
        )
        if price_cents is None:
            return

        margin_pct = self._parse_int(row.get("margin_pct", "0"), line_number, "margin_pct", result)
        if margin_pct is None:
            return

        min_stock_qty = self._parse_int(
            row.get("min_stock_qty", "0"), line_number, "min_stock_qty", result
        )
        if min_stock_qty is None:
            return

        stock_qty = self._parse_int(row.get("stock_qty", "0"), line_number, "stock_qty", result)
        if stock_qty is None:
            return

        unit = (row.get("unit") or "un").strip() or "un"
        sold_by_weight = (row.get("sold_by_weight") or "false").strip().lower() in (
            "true",
            "1",
            "sim",
            "s",
            "yes",
        )
        active = (row.get("active") or "true").strip().lower() in (
            "true",
            "1",
            "sim",
            "s",
            "yes",
        )

        imported_product = ImportedProduct(
            sku=sku,
            name=name,
            description=(row.get("description") or "").strip(),
            unit=unit,
            cost_cents=cost_cents,
            margin_pct=margin_pct,
            price_cents=price_cents,
            min_stock_qty=min_stock_qty,
            stock_qty=stock_qty,
            sold_by_weight=sold_by_weight,
            active=active,
            category_name=(row.get("category_name") or "").strip(),
            supplier_name=(row.get("supplier_name") or "").strip(),
        )

        result.imported_products.append(imported_product)
        result.imported_count += 1

        # Persiste o produto no banco via port do catálogo
        product_snapshot = SimpleNamespace(
            sku=imported_product.sku,
            name=imported_product.name,
            description=imported_product.description,
            unit=imported_product.unit,
            cost_cents=imported_product.cost_cents,
            margin_pct=imported_product.margin_pct,
            price_cents=imported_product.price_cents,
            stock_qty=imported_product.stock_qty,
            min_stock_qty=imported_product.min_stock_qty,
            sold_by_weight=imported_product.sold_by_weight,
            active=imported_product.active,
            company_id=company_id,
        )
        self._product_repo.add_snapshot(product_snapshot)

    def _parse_money(
        self,
        value: str,
        line_number: int,
        field_name: str,
        result: ImportResult,
    ) -> int | None:
        """Converte valor monetário (string com vírgula decimal pt-BR) para centavos.

        Nunca usa float. Usa Decimal para precisão.
        Se o valor já contém separador decimal (vírgula ou ponto), trata como
        reais e converte para centavos. Se não houver separador, já está em centavos.
        """
        if value is None or value.strip() == "":
            return 0

        original_value = value.strip()
        value = original_value.replace(".", "").replace(",", ".")
        try:
            decimal_value = Decimal(value)
            # Se o valor original tem separador decimal, está em reais -> converte para centavos
            # Se não tem separador, já está em centavos
            if "," in original_value or "." in original_value:
                cents = int(decimal_value * 100)
            else:
                cents = int(decimal_value)
            return cents
        except (InvalidOperation, ValueError):
            result.errors.append(
                ImportError(
                    line_number=line_number,
                    field=field_name,
                    message=f"Preço inválido: {value}",
                    value=value,
                )
            )
            result.error_count += 1
            return None

    def _parse_int(
        self,
        value: str,
        line_number: int,
        field_name: str,
        result: ImportResult,
    ) -> int | None:
        """Converte valor inteiro."""
        if value is None or value.strip() == "":
            return 0

        value = value.strip()
        try:
            return int(value)
        except ValueError:
            result.errors.append(
                ImportError(
                    line_number=line_number,
                    field=field_name,
                    message=f"Valor inválido: {value}",
                    value=value,
                )
            )
            result.error_count += 1
            return None
