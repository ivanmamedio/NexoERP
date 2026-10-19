"""Base domain events for the in-memory EventBus.

Modules publish these events so cross-cutting concerns (audit, cache
invalidation, notifications) can react without depending on each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class DomainEvent:
    """Base class for all domain events."""

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class EntityCreated(DomainEvent):
    """An entity was created."""

    entity_type: str = ""
    entity_id: int | None = None
    user_id: int | None = None
    username: str = ""
    after: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class EntityUpdated(DomainEvent):
    """An entity was updated."""

    entity_type: str = ""
    entity_id: int | None = None
    user_id: int | None = None
    username: str = ""
    before: dict[str, object] = field(default_factory=dict)
    after: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class EntityDeleted(DomainEvent):
    """An entity was deleted."""

    entity_type: str = ""
    entity_id: int | None = None
    user_id: int | None = None
    username: str = ""
    before: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class UserLoggedIn(DomainEvent):
    """A user successfully logged in."""

    user_id: int | None = None
    username: str = ""


@dataclass(slots=True)
class SaleCompleted(DomainEvent):
    """Uma venda foi finalizada.

    Publicado por FinalizeSale. Os módulos catalog, cash, treasury e audit
    reagem via EventBus, dentro da mesma transação.
    """

    sale_id: int = 0
    company_id: int | None = None
    session_id: int | None = None
    user_id: int | None = None
    username: str = ""
    total_cents: int = 0
    cash_cents: int = 0
    pix_cents: int = 0
    card_cents: int = 0
    items: list[dict[str, object]] = field(default_factory=list)
    """Itens vendidos: [{"product_id": int, "quantity_thousandths": int}, ...]."""
