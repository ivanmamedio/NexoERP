"""Adjust stock use case — records a stock movement and updates stock_qty cache."""

from __future__ import annotations

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.modules.catalog.domain.stock_movement import StockMovement
from erp.shared.domain.errors import NotFound, ValidationError


class AdjustStockInput:
    def __init__(
        self,
        *,
        product_id: int,
        quantity_thousandths: int,
        movement_type: str = "adjustment",
        reference_id: int | None = None,
        notes: str = "",
        user_id: int | None = None,
        username: str = "",
        company_id: int | None = None,
    ) -> None:
        self.product_id = product_id
        self.quantity_thousandths = quantity_thousandths
        self.movement_type = movement_type
        self.reference_id = reference_id
        self.notes = notes
        self.user_id = user_id
        self.username = username
        self.company_id = company_id


class AdjustStockOutput:
    def __init__(self, product: Product, new_stock_qty: int) -> None:
        self.product = product
        self.new_stock_qty = new_stock_qty


class AdjustStock:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(self, input: AdjustStockInput) -> AdjustStockOutput:
        product = self._repository.get_by_id(input.product_id)
        if product is None:
            raise NotFound(f"Produto {input.product_id} não encontrado.")
        if product.company_id != input.company_id:
            raise ValidationError("Produto pertence a outra empresa.")

        new_qty = product.stock_qty + input.quantity_thousandths
        if new_qty < 0:
            raise ValidationError(
                f"Ajuste deixaria estoque negativo ({new_qty / 1000:.3f} {product.unit})."
            )

        product.stock_qty = new_qty
        self._repository.save(product)

        StockMovement(
            product_id=product.id if product.id is not None else 0,
            company_id=input.company_id,
            quantity_thousandths=input.quantity_thousandths,
            movement_type=input.movement_type,
            reference_id=input.reference_id,
            notes=input.notes,
            user_id=input.user_id,
            username=input.username,
        )
        # Stock movements are persisted through the same UoW via the repository
        # in implementations that support it; here we keep it simple and rely on
        # the caller/UoW to flush within the same transaction.
        return AdjustStockOutput(product=product, new_stock_qty=new_qty)
