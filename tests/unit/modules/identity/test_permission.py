"""Unit tests for Permission domain value object."""

from __future__ import annotations

import pytest

from erp.modules.identity.domain.permission import (
    ALL_PERMISSIONS,
    PERMISSION_CASH_SANGRIA,
    PERMISSION_PRODUCT_PRICE_UPDATE,
    PERMISSION_TREASURY_VIEW,
    Permission,
)


def test_permission_creation_valid() -> None:
    perm = Permission("product.price.update")
    assert perm.code == "product.price.update"


def test_permission_empty_code_raises() -> None:
    with pytest.raises(ValueError):
        Permission("")


def test_permission_space_in_code_raises() -> None:
    with pytest.raises(ValueError):
        Permission("product price update")


def test_all_permissions_contains_expected() -> None:
    codes = {p.code for p in ALL_PERMISSIONS}
    assert "product.price.update" in codes
    assert "treasury.view" in codes
    assert "cash.sangria" in codes


def test_caixa_role_does_not_have_price_update_or_treasury_view() -> None:
    """O Caixa NÃO tem product.price.update nem treasury.view."""
    from erp.modules.identity.domain.permission import ROLE_PERMISSIONS

    caixa_permissions = ROLE_PERMISSIONS["Caixa"]
    assert "product.price.update" not in caixa_permissions
    assert "treasury.view" not in caixa_permissions


def test_administrador_has_all_permissions() -> None:
    from erp.modules.identity.domain.permission import ROLE_PERMISSIONS

    admin_permissions = ROLE_PERMISSIONS["Administrador"]
    for perm in ALL_PERMISSIONS:
        assert perm.code in admin_permissions


def test_financeiro_has_treasury_view() -> None:
    from erp.modules.identity.domain.permission import ROLE_PERMISSIONS

    financeiro_permissions = ROLE_PERMISSIONS["Financeiro"]
    assert "treasury.view" in financeiro_permissions
    assert "product.price.update" not in financeiro_permissions
