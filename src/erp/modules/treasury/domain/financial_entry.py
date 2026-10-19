"""Financial entry domain entity (livro-razão)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class FinancialEntry(Entity):
    """Lançamento financeiro no livro-razão."""

    company_id: int | None = None
    date: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    type: str = ""  # "receivable" ou "payable"
    amount_cents: int = 0
    category_id: int | None = None
    source_type: str = ""  # "sale", "cash_session", etc.
    source_id: int | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if self.type:
            self.type = self.type.strip().lower()
        if self.source_type:
            self.source_type = self.source_type.strip().lower()
