"""CSV product parser for import module."""

from __future__ import annotations

import csv
from pathlib import Path

from erp.modules.import_csv.domain.import_result import (
    ImportError,
)


class CSVProductParser:
    """Parser de arquivos CSV de produtos."""

    REQUIRED_COLUMNS = frozenset({"sku", "name"})
    OPTIONAL_COLUMNS = frozenset(
        {
            "description",
            "unit",
            "cost_cents",
            "margin_pct",
            "price_cents",
            "min_stock_qty",
            "stock_qty",
            "sold_by_weight",
            "active",
            "category_name",
            "supplier_name",
        }
    )

    def parse(self, file_path: str | Path, encoding: str = "utf-8") -> list[dict[str, str]]:
        """Faz parse de um arquivo CSV e retorna lista de dicionários."""

        with open(file_path, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def validate_headers(self, headers: list[str]) -> list[ImportError]:
        """Valida que as colunas obrigatórias existem."""

        errors: list[ImportError] = []
        header_set = {h.strip().lower() for h in headers if h}
        missing = self.REQUIRED_COLUMNS - header_set

        if missing:
            errors.append(
                ImportError(
                    line_number=1,
                    field="header",
                    message=f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}",
                    value=", ".join(sorted(header_set)),
                )
            )

        return errors

    def normalize_row(self, row: dict[str, str]) -> dict[str, str]:
        """Normaliza uma linha do CSV (remove espaços, normaliza nomes)."""

        normalized: dict[str, str] = {}
        for key, value in row.items():
            if key is None:
                continue
            normalized_key = key.strip().lower() if key else ""
            normalized_value = (value or "").strip() if value else ""
            normalized[normalized_key] = normalized_value

        return normalized
