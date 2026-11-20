"""Shared domain types used across multiple modules.

This module provides common domain types to avoid circular imports
and reduce cross-module dependencies at the domain layer.
"""

from __future__ import annotations

from dataclasses import dataclass


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
