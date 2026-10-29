"""Permission value object — código tipo 'product.price.update'."""

from __future__ import annotations

from dataclasses import dataclass, field

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class Permission(Entity):
    """Código de permissão do sistema.

    Exemplos: "product.price.update", "treasury.view", "cash.sangria",
    "sale.discount", "sale.cancel".
    """

    code: str
    id: int | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not self.code or not isinstance(self.code, str):
            raise ValueError("Permission code must be a non-empty string")
        if " " in self.code:
            raise ValueError("Permission code must not contain spaces")

    def __hash__(self) -> int:
        return hash(self.code)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return False
        return self.code == other.code


# Permissões do sistema (conforme QWEN.md e fases subsequentes)
PERMISSION_PRODUCT_PRICE_UPDATE = Permission("product.price.update")
PERMISSION_TREASURY_VIEW = Permission("treasury.view")
PERMISSION_CASH_SANGRIA = Permission("cash.sangria")
PERMISSION_SALE_VIEW = Permission("sale.view")
PERMISSION_SALE_DISCOUNT = Permission("sale.discount")
PERMISSION_SALE_CANCEL = Permission("sale.cancel")
PERMISSION_USER_MANAGE = Permission("user.manage")
PERMISSION_COMPANY_MANAGE = Permission("company.manage")
PERMISSION_CATALOG_MANAGE = Permission("catalog.manage")
PERMISSION_CASH_OPEN_CLOSE = Permission("cash.open_close")
PERMISSION_RECEIPT_PRINT = Permission("receipt.print")
PERMISSION_REPORTS_VIEW = Permission("reports.view")
PERMISSION_BACKUP_MANAGE = Permission("backup.manage")
PERMISSION_SETTINGS_UPDATE = Permission("settings.update")
PERMISSION_CUSTOMER_CREATE = Permission("customer.create")
PERMISSION_CUSTOMER_UPDATE = Permission("customer.update")
PERMISSION_CUSTOMER_READ = Permission("customer.read")
PERMISSION_PRODUCT_IMPORT = Permission("product.import")

ALL_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        PERMISSION_PRODUCT_PRICE_UPDATE,
        PERMISSION_TREASURY_VIEW,
        PERMISSION_CASH_SANGRIA,
        PERMISSION_SALE_VIEW,
        PERMISSION_SALE_DISCOUNT,
        PERMISSION_SALE_CANCEL,
        PERMISSION_USER_MANAGE,
        PERMISSION_COMPANY_MANAGE,
        PERMISSION_CATALOG_MANAGE,
        PERMISSION_CASH_OPEN_CLOSE,
        PERMISSION_RECEIPT_PRINT,
        PERMISSION_REPORTS_VIEW,
        PERMISSION_BACKUP_MANAGE,
        PERMISSION_SETTINGS_UPDATE,
        PERMISSION_CUSTOMER_CREATE,
        PERMISSION_CUSTOMER_UPDATE,
        PERMISSION_CUSTOMER_READ,
        PERMISSION_PRODUCT_IMPORT,
    }
)

# Permissões por papel (seed)
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "Administrador": frozenset({p.code for p in ALL_PERMISSIONS}),
    "Gerente": frozenset(
        {
            "product.price.update",
            "treasury.view",
            "cash.sangria",
            "sale.view",
            "sale.discount",
            "sale.cancel",
            "user.manage",
            "company.manage",
            "catalog.manage",
            "cash.open_close",
            "receipt.print",
            "reports.view",
            "settings.update",
            "customer.create",
            "customer.update",
            "customer.read",
            "product.import",
        }
    ),
    "Caixa": frozenset(
        {
            "sale.view",
            "sale.discount",
            "sale.cancel",
            "cash.open_close",
            "receipt.print",
            "customer.read",
        }
    ),
    "Financeiro": frozenset(
        {
            "treasury.view",
            "reports.view",
        }
    ),
}
