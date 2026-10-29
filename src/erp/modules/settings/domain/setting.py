"""Setting domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Setting(Entity):
    """Configuração por empresa (chave-valor tipado)."""

    company_id: int = 0
    key: str = ""
    value: str = ""
    value_type: str = "string"
    updated_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    updated_by_user_id: int | None = None
    updated_by_username: str = ""
