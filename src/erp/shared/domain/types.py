"""Shared domain types used across multiple modules.

This module provides common domain types to avoid circular imports
and reduce cross-module dependencies at the domain layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    """Base entity with identity."""

    id: int | None = field(default=None, init=True)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity) or type(self) is not type(other):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))


# Re-export from shared.domain.entities for backward compatibility
# (kept here to avoid import cycles during gradual migration)
__all__ = ["Entity"]


# Common value objects and types that multiple modules need
@dataclass(frozen=True, slots=True)
class CompanyRef:
    """Lightweight reference to a company (for cross-module use)."""

    id: int
    name: str
    trade_name: str


@dataclass(frozen=True, slots=True)
class UserRef:
    """Lightweight reference to a user (for cross-module use)."""

    id: int
    username: str
    company_id: int | None


@dataclass(frozen=True, slots=True)
class ProductRef:
    """Lightweight reference to a product (for cross-module use)."""

    id: int
    sku: str
    name: str
    price_cents: int
    unit: str
    stock_qty: int
    company_id: int
