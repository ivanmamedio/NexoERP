"""Cash movement domain entity (sangria, suprimento, venda)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


class MovementType:
    """Tipos de movimento de caixa."""

    SUPRIMENTO = "suprimento"
    SANGRIA = "sangria"
    VENDA_DINHEIRO = "venda_dinheiro"


@dataclass(slots=True)
class CashMovement(Entity):
    """Movimento financeiro de uma sessão de caixa."""

    session_id: int = 0
    company_id: int | None = None
    movement_type: str = ""  # suprimento, sangria, venda_dinheiro
    amount_cents: int = 0  # sempre positivo; tipo define sinal
    description: str = ""
    user_id: int | None = None
    username: str = ""
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.movement_type:
            self.movement_type = self.movement_type.strip().lower()

    def is_sangria(self) -> bool:
        return self.movement_type == MovementType.SANGRIA

    def is_suprimento(self) -> bool:
        return self.movement_type == MovementType.SUPRIMENTO

    def is_venda_dinheiro(self) -> bool:
        return self.movement_type == MovementType.VENDA_DINHEIRO

    def signed_amount_cents(self) -> int:
        """Retorna o valor com sinal: sangria negativa, suprimento/venda positiva."""
        if self.is_sangria():
            return -abs(self.amount_cents)
        return abs(self.amount_cents)
