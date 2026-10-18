"""Sale payment domain entity (mixed payments and change)."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


class PaymentMethod:
    """Meios de pagamento."""

    CASH = "cash"
    PIX = "pix"
    CARD = "card"


@dataclass(slots=True)
class SalePayment(Entity):
    """Pagamento de uma venda (misto permitido)."""

    sale_id: int = 0
    company_id: int | None = None
    method: str = ""  # cash, pix, card
    amount_cents: int = 0
    change_cents: int = 0  # troco atribuído a este pagamento em dinheiro

    def __post_init__(self) -> None:
        if self.method:
            self.method = self.method.strip().lower()

    def is_cash(self) -> bool:
        return self.method == PaymentMethod.CASH
