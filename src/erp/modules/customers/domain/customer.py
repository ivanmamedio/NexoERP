"""Customers domain entities."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Customer(Entity):
    """Cadastro de cliente (dados mínimos, LGPD)."""

    company_id: int = 0
    name: str = ""
    phone: str = ""
    document: str | None = None  # CPF/CNPJ opcional
    credit_limit_cents: int = 0
    is_active: bool = True
