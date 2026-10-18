"""Supplier domain entity."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Supplier(Entity):
    """Fornecedor de produtos."""

    name: str = ""
    trade_name: str = ""
    tax_id: str = ""
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    is_active: bool = True
    company_id: int | None = None

    def __post_init__(self) -> None:
        if self.name:
            self.name = self.name.strip()
        if not self.trade_name:
            self.trade_name = self.name
