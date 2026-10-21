"""Cancel sale / cancel item use case — estorno de estoque, permissão sale.cancel."""

from __future__ import annotations

from erp.modules.sales.application.ports import (
    ProductCatalogPort,
    SaleItemRepository,
    SaleRepository,
)
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError


class CancelSaleInput:
    def __init__(
        self,
        *,
        sale_id: int,
        reason: str,
        user_id: int | None,
        username: str,
        company_id: int | None = None,
    ) -> None:
        self.sale_id = sale_id
        self.reason = reason
        self.user_id = user_id
        self.username = username
        self.company_id = company_id


class CancelItemInput:
    def __init__(
        self,
        *,
        item_id: int,
        reason: str,
        user_id: int | None,
        username: str,
        company_id: int | None = None,
    ) -> None:
        self.item_id = item_id
        self.reason = reason
        self.user_id = user_id
        self.username = username
        self.company_id = company_id


class CancelSale:
    """Cancela venda inteira (estorna estoque)."""

    def __init__(
        self,
        sale_repo: SaleRepository,
        item_repo: SaleItemRepository,
        product_repo: ProductCatalogPort,
        user_permissions: set[str],
    ) -> None:
        self._sale_repo = sale_repo
        self._item_repo = item_repo
        self._product_repo = product_repo
        self._user_permissions = user_permissions

    def execute(self, input: CancelSaleInput) -> None:
        if "sale.cancel" not in self._user_permissions:
            raise PermissionDenied("Usuário não tem permissão para cancelar vendas (sale.cancel).")
        sale = self._sale_repo.get_by_id(input.sale_id, company_id=input.company_id)
        if sale is None:
            raise NotFound(f"Venda {input.sale_id} não encontrada.")
        if sale.is_cancelled():
            raise ValidationError("Venda já está cancelada.")

        sale.cancel(reason=input.reason, user_id=input.user_id, username=input.username)
        self._sale_repo.save(sale)

        # Estorna estoque apenas se a venda já tinha sido finalizada
        if sale.is_cancelled() and sale.finalized_at is not None:
            items = self._item_repo.list_by_sale(sale.id or 0)
            for item in items:
                if item.product_id is None or item.cancelled:
                    continue
                product = self._product_repo.get_by_id(item.product_id)
                if product is None:
                    continue
                product.stock_qty += item.quantity_thousandths
                self._product_repo.save(product)


class CancelItem:
    """Cancela um item de venda em rascunho (sem estorno, venda ainda não finalizada)."""

    def __init__(
        self,
        sale_repo: SaleRepository,
        item_repo: SaleItemRepository,
        user_permissions: set[str],
    ) -> None:
        self._sale_repo = sale_repo
        self._item_repo = item_repo
        self._user_permissions = user_permissions

    def execute(self, input: CancelItemInput) -> None:
        if "sale.cancel" not in self._user_permissions:
            raise PermissionDenied("Usuário não tem permissão para cancelar itens (sale.cancel).")
        item = self._item_repo.get_by_id(input.item_id)
        if item is None:
            raise NotFound(f"Item {input.item_id} não encontrado.")

        sale = self._sale_repo.get_by_id(item.sale_id, company_id=input.company_id)
        if sale is None:
            raise NotFound(f"Venda {item.sale_id} não encontrada.")
        if not sale.is_draft():
            raise ValidationError("Só é possível cancelar item de venda em rascunho.")

        item.cancelled = True
        item.cancel_reason = input.reason
        self._item_repo.save(item)

        # Recalcula subtotal
        items = self._item_repo.list_by_sale(sale.id or 0)
        subtotal = sum(i.line_total_cents for i in items if not i.cancelled)
        sale.recalculate(subtotal)
        self._sale_repo.save(sale)
