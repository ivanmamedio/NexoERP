"""Cash closing report (dados estruturados do fechamento do turno)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class CashClosingReport:
    """Relatório estruturado do fechamento de caixa (sem UI ainda)."""

    session_id: int = 0
    register_name: str = ""
    company_id: int | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    opened_by_username: str = ""
    closed_by_username: str = ""

    opening_amount_cents: int = 0
    total_sales_cents: int = 0
    total_suprimentos_cents: int = 0
    total_sangrias_cents: int = 0
    total_pix_cents: int = 0
    total_card_cents: int = 0
    expected_cash_cents: int = 0
    counted_cash_cents: int = 0
    difference_cents: int = 0
    blind_close: bool = False

    status: str = "closed"
