"""Application module init for purchases."""

from erp.modules.purchases.application.count_inventory import (
    CountInventory,
    InventoryCountInput,
    InventoryCountOutput,
)
from erp.modules.purchases.application.register_purchase import (
    PurchaseItemInput,
    RegisterPurchase,
    RegisterPurchaseInput,
    RegisterPurchaseOutput,
)

__all__ = [
    "CountInventory",
    "InventoryCountInput",
    "InventoryCountOutput",
    "PurchaseItemInput",
    "RegisterPurchase",
    "RegisterPurchaseInput",
    "RegisterPurchaseOutput",
]
