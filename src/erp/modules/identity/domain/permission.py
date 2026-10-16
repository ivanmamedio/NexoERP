"""Permission value object — código tipo 'product.price.update'."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    """Código de permissão do sistema.

    Exemplos: "product.price.update", "treasury.view", "cash.sangria",
    "sale.discount", "sale.cancel".
    """

    code: str

    def __post_init__(self) -> None:
        if not self.code or not isinstance(self.code, str):
            raise ValueError("Permission code must be a non-empty string")
        if " " in self.code:
            raise ValueError("Permission code must not contain spaces")


# Permissões do sistema (conforme QWEN.md e fases subsequentes)
PERMISSION_PRODUCT_PRICE_UPDATE = Permission("product.price.update")
PERMISSION_TREASURY_VIEW = Permission("treasury.view")
PERMISSION_CASH_SANGRIA = Permission("cash.sangria")
PERMISSION_SALE_DISCOUNT = Permission("sale.discount")
PERMISSION_SALE_CANCEL = Permission("sale.cancel")
PERMISSION_USER_MANAGE = Permission("user.manage")
PERMISSION_COMPANY_MANAGE = Permission("company.manage")
PERMISSION_CATALOG_MANAGE = Permission("catalog.manage")
PERMISSION_CASH_OPEN_CLOSE = Permission("cash.open_close")
PERMISSION_RECEIPT_PRINT = Permission("receipt.print")
PERMISSION_REPORTS_VIEW = Permission("reports.view")
PERMISSION_BACKUP_MANAGE = Permission("backup.manage")

ALL_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        PERMISSION_PRODUCT_PRICE_UPDATE,
        PERMISSION_TREASURY_VIEW,
        PERMISSION_CASH_SANGRIA,
        PERMISSION_SALE_DISCOUNT,
        PERMISSION_SALE_CANCEL,
        PERMISSION_USER_MANAGE,
        PERMISSION_COMPANY_MANAGE,
        PERMISSION_CATALOG_MANAGE,
        PERMISSION_CASH_OPEN_CLOSE,
        PERMISSION_RECEIPT_PRINT,
        PERMISSION_REPORTS_VIEW,
        PERMISSION_BACKUP_MANAGE,
    }
)

# Permissões por papel (seed)
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "Administrador": {p.code for p in ALL_PERMISSIONS},
    "Gerente": {
        "product.price.update",
        "treasury.view",
        "cash.sangria",
        "sale.discount",
        "sale.cancel",
        "user.manage",
        "company.manage",
        "catalog.manage",
        "cash.open_close",
        "receipt.print",
        "reports.view",
    },
    "Caixa": {
        "sale.discount",
        "sale.cancel",
        "cash.open_close",
        "receipt.print",
    },
    "Financeiro": {
        "treasury.view",
        "reports.view",
    },
}
