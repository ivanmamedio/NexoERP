"""Role entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Role(Entity):
    """Papel de usuário no sistema (ex.: Administrador, Caixa, Financeiro)."""

    id: int | None = field(default=None)
    name: str = field(default="")
    description: str = field(default="")
    is_active: bool = field(default=True)
