"""Cash session domain entity (sessão de caixa aberta/fechada)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class CashSession(Entity):
    """Sessão de caixa: abertura, movimentos e fechamento."""

    register_id: int = 0
    company_id: int | None = None
    opened_by_user_id: int | None = None
    opened_by_username: str = ""
    opened_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    opening_amount_cents: int = 0  # dinheiro em caixa na abertura (centavos)

    closed_by_user_id: int | None = None
    closed_by_username: str = ""
    closed_at: datetime | None = None
    closing_amount_cents: int = 0  # dinheiro contado no fechamento (centavos)

    # Totais calculados no fechamento
    total_sales_cents: int = 0  # vendas em dinheiro
    total_suprimentos_cents: int = 0
    total_sangrias_cents: int = 0
    total_pix_cents: int = 0
    total_card_cents: int = 0
    expected_cash_cents: int = 0  # esperado_dinheiro
    difference_cents: int = 0  # diferença = contado - esperado

    status: str = "open"  # open, closed
    closed: bool = False
    blind_close: bool = False  # fechamento cego (não confere valores)

    def is_open(self) -> bool:
        return self.status == "open"

    def is_closed(self) -> bool:
        return self.status == "closed"

    def calculate_expected_cash(self) -> int:
        """esperado_dinheiro = abertura + vendas em dinheiro + suprimentos - sangrias."""
        return (
            self.opening_amount_cents
            + self.total_sales_cents
            + self.total_suprimentos_cents
            - self.total_sangrias_cents
        )

    def close(
        self,
        *,
        closing_amount_cents: int,
        closed_by_user_id: int | None,
        closed_by_username: str,
        blind_close: bool = False,
    ) -> None:
        if self.is_closed():
            raise ValueError("Sessão de caixa já está fechada.")
        self.closed = True
        self.status = "closed"
        self.closed_at = datetime.now(UTC)
        self.closed_by_user_id = closed_by_user_id
        self.closed_by_username = closed_by_username
        self.closing_amount_cents = closing_amount_cents
        self.blind_close = blind_close
        self.expected_cash_cents = self.calculate_expected_cash()
        self.difference_cents = closing_amount_cents - self.expected_cash_cents
