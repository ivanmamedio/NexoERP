"""RegisterPurchase use case — entrada de mercadoria."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.purchases.application.ports import (
    PurchaseItemRepository,
    PurchaseRepository,
)
from erp.modules.purchases.domain.purchase import Purchase, PurchaseItem
from erp.shared.domain.errors import PermissionDenied


@dataclass(slots=True, frozen=True)
class PurchaseItemInput:
    product_id: int
    quantity_thousandths: int
    unit_cost_cents: int


@dataclass(slots=True, frozen=True)
class RegisterPurchaseInput:
    supplier_id: int | None
    items: list[PurchaseItemInput]
    user_id: int | None
    username: str
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class RegisterPurchaseOutput:
    purchase_id: int
    total_cents: int


class RegisterPurchase:
    """Registra uma entrada de mercadoria (compra).

    Exige permissão catalog.cost.update para atualizar o custo do produto.
    """

    def __init__(
        self,
        purchase_repo: PurchaseRepository,
        item_repo: PurchaseItemRepository,
        user_permissions: set[str],
    ) -> None:
        self._purchase_repo = purchase_repo
        self._item_repo = item_repo
        self._user_permissions = user_permissions

    def execute(self, input: RegisterPurchaseInput) -> RegisterPurchaseOutput:
        if "catalog.cost.update" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para registrar compra de mercadoria "
                "(catalog.cost.update)."
            )

        if not input.items:
            from erp.shared.domain.errors import ValidationError

            raise ValidationError("A compra deve ter pelo menos um item.")

        total_cents = 0
        purchase_items = []

        for item_input in input.items:
            line_total = item_input.quantity_thousandths * item_input.unit_cost_cents // 1000
            total_cents += line_total

            item = PurchaseItem(
                purchase_id=0,  # definido após salvar a compra
                product_id=item_input.product_id,
                quantity_thousandths=item_input.quantity_thousandths,
                unit_cost_cents=item_input.unit_cost_cents,
                line_total_cents=line_total,
            )
            purchase_items.append(item)

        purchase = Purchase(
            supplier_id=input.supplier_id,
            user_id=input.user_id,
            username=input.username,
            company_id=input.company_id or 0,
            total_cents=total_cents,
            status="registered",
        )
        self._purchase_repo.add(purchase)

        for item in purchase_items:
            item.purchase_id = purchase.id or 0
            self._item_repo.add(item)

        return RegisterPurchaseOutput(
            purchase_id=purchase.id or 0,
            total_cents=total_cents,
        )
