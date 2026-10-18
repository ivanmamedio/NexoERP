"""Cash register domain entity (terminal/caixa)."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class CashRegister(Entity):
    """Terminal/caixa físico da empresa."""

    name: str = ""
    terminal_code: str = ""
    company_id: int | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if self.name:
            self.name = self.name.strip()
        if self.terminal_code:
            self.terminal_code = self.terminal_code.strip().upper()
