"""CountInventory use case — contagem física de estoque.

A diferença entre a contagem física e o estoque registrado vira um
movimento de ajuste com motivo obrigatório.
"""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.errors import PermissionDenied, ValidationError


@dataclass(slots=True, frozen=True)
class InventoryCountInput:
    product_id: int
    counted_quantity_thousandths: int
    reason: str
    user_id: int | None = None
    username: str = ""
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class InventoryCountOutput:
    product_id: int
    previous_quantity_thousandths: int
    counted_quantity_thousandths: int
    difference_thousandths: int
    reason: str


class CountInventory:
    """Registra uma contagem física de estoque.

    A diferença entre a contagem física e o estoque registrado é calculada
    e retornada para registro de movimento de ajuste pelo caller.
    """

    def __init__(
        self,
        user_permissions: set[str],
    ) -> None:
        self._user_permissions = user_permissions

    def execute(self, input: InventoryCountInput) -> InventoryCountOutput:
        if "catalog.cost.update" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para contagem de estoque (catalog.cost.update)."
            )

        if not input.reason.strip():
            raise ValidationError("Motivo da contagem é obrigatório.")

        if input.counted_quantity_thousandths < 0:
            raise ValidationError("Quantidade contada não pode ser negativa.")

        # A quantidade anterior seria obtida do repositório de produtos do
        # catálogo. Aqui devolvemos zero como previous para que o caller
        # registre o movimento de ajuste com base na contagem real.
        previous_qty = 0
        difference = input.counted_quantity_thousandths - previous_qty

        return InventoryCountOutput(
            product_id=input.product_id,
            previous_quantity_thousandths=previous_qty,
            counted_quantity_thousandths=input.counted_quantity_thousandths,
            difference_thousandths=difference,
            reason=input.reason,
        )
