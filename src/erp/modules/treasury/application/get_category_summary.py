"""Get category summary use case (despesas/receitas por categoria)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from erp.modules.treasury.application.ports import (
    FinancialCategoryRepository,
    FinancialEntryRepository,
)


@dataclass(slots=True, frozen=True)
class CategorySummaryRow:
    category_id: int
    category_name: str
    category_kind: str  # "expense", "income", "transfer"
    total_cents: int
    entry_count: int


@dataclass(slots=True, frozen=True)
class GetCategorySummaryInput:
    start_date: datetime
    end_date: datetime
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class GetCategorySummaryOutput:
    rows: tuple[CategorySummaryRow, ...]
    total_income_cents: int
    total_expense_cents: int
    net_cents: int


class GetCategorySummary:
    """Resumo de despesas e receitas por categoria no período."""

    def __init__(
        self,
        entry_repo: FinancialEntryRepository,
        category_repo: FinancialCategoryRepository,
    ) -> None:
        self._entry_repo = entry_repo
        self._category_repo = category_repo

    def execute(self, input_data: GetCategorySummaryInput) -> GetCategorySummaryOutput:
        entries = self._entry_repo.list_by_period(
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            company_id=input_data.company_id,
        )

        # Buscar todas as categorias para mapear id -> nome/kind
        categories = self._category_repo.list_all(company_id=input_data.company_id)
        cat_map = {c.id: c for c in categories if c.id is not None}

        # Agrupar por categoria
        summary: dict[int, dict[str, Any]] = {}
        for entry in entries:
            cat_id = entry.category_id or 0
            if cat_id not in summary:
                cat = cat_map.get(cat_id)
                summary[cat_id] = {
                    "category_id": cat_id,
                    "category_name": cat.name if cat else "Sem categoria",
                    "category_kind": cat.kind if cat else "expense",
                    "total_cents": 0,
                    "entry_count": 0,
                }
            summary[cat_id]["total_cents"] += entry.amount_cents
            summary[cat_id]["entry_count"] += 1

        rows = tuple(
            CategorySummaryRow(
                category_id=v["category_id"],
                category_name=v["category_name"],
                category_kind=v["category_kind"],
                total_cents=v["total_cents"],
                entry_count=v["entry_count"],
            )
            for v in summary.values()
        )

        # Ordenar: receitas primeiro (maior valor), depois despesas
        rows = tuple(sorted(rows, key=lambda r: (r.category_kind != "income", -r.total_cents)))

        total_income = sum(r.total_cents for r in rows if r.category_kind == "income")
        total_expense = sum(r.total_cents for r in rows if r.category_kind == "expense")

        return GetCategorySummaryOutput(
            rows=rows,
            total_income_cents=total_income,
            total_expense_cents=total_expense,
            net_cents=total_income - total_expense,
        )
