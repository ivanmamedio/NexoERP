"""Unit tests for Role domain entity."""

from __future__ import annotations

from erp.modules.identity.domain.role import Role


def test_role_creation() -> None:
    role = Role(name="Caixa", description="Papel de caixa", is_active=True)
    assert role.name == "Caixa"
    assert role.description == "Papel de caixa"
    assert role.is_active is True
