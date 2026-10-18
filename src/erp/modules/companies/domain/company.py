"""Company domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Company(Entity):
    """Empresa/estabelecimento do sistema."""

    name: str = ""
    trade_name: str = ""
    tax_id: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    active: bool = True
    created_at: str | None = None
    updated_at: str | None = None
    company_id: int | None = None

    def __post_init__(self) -> None:
        if self.name:
            self.name = self.name.strip()
        if not self.trade_name:
            self.trade_name = self.name

