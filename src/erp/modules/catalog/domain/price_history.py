"""Price history domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class PriceHistory(Entity):
    """Registro de alteração de preço de um produto (auditoria de precificação)."""

    product_id: int = 0
    company_id: int | None = None
    old_price_cents: int = 0
    new_price_cents: int = 0
    changed_by_user_id: int | None = None
    changed_by_username: str = ""
    changed_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    reason: str = ""
