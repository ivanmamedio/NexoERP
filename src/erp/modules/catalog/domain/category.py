"""Category domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Category(Entity):
    """Categoria hierárquica de produtos."""

    name: str = ""
    description: str = ""
    parent_id: int | None = None
    is_active: bool = True
    company_id: int | None = None

    def __post_init__(self) -> None:
        if self.name:
            self.name = self.name.strip()
