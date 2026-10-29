"""Domain entities for CSV import result."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ImportError:
    """Erro encontrado durante a importação de uma linha."""

    line_number: int
    field: str
    message: str
    value: str = ""


@dataclass(slots=True)
class ImportedProduct:
    """Produto importado com sucesso do CSV."""

    sku: str
    name: str
    description: str = ""
    unit: str = "un"
    cost_cents: int = 0
    margin_pct: int = 0
    price_cents: int = 0
    min_stock_qty: int = 0
    stock_qty: int = 0
    sold_by_weight: bool = False
    active: bool = True
    category_name: str = ""
    supplier_name: str = ""


@dataclass(slots=True)
class ImportResult:
    """Resultado da importação de um CSV."""

    total_lines: int = 0
    imported_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
    imported_products: list[ImportedProduct] = field(default_factory=list)
    errors: list[ImportError] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.imported_count / self.total_lines) * 100

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
