"""Financial category domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class FinancialCategory(Entity):
    """Categoria financeira para classificação de lançamentos."""

    company_id: int | None = None
    name: str = ""
    kind: str = ""  # "expense", "income", "transfer"
    description: str = ""
    is_active: bool = field(default=True)

    def __post_init__(self) -> None:
        if self.kind:
            self.kind = self.kind.strip().lower()
        if self.name:
            self.name = self.name.strip()
