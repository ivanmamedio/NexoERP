"""GetSaleState query — estado atual da venda para a tela do PDV."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.sales.application.ports import SaleItemRepository, SaleRepository
from erp.shared.domain.errors import NotFound


@dataclass(slots=True, frozen=True)
class SaleItemView:
    """Visão imutável de um item de venda para exibição."""

    item_id: int
    description: str
    quantity_thousandths: int
    unit: str
    unit_price_cents: int
    line_total_cents: int
    cancelled: bool


@dataclass(slots=True, frozen=True)
class SaleStateOutput:
    """Estado atual da venda (totais e itens)."""

    sale_id: int
    status: str
    subtotal_cents: int
    discount_cents: int
    total_cents: int
    items: tuple[SaleItemView, ...]


class GetSaleState:
    """Lê a venda e seus itens para montar a visão de tela."""

    def __init__(
        self,
        sale_repo: SaleRepository,
        item_repo: SaleItemRepository,
    ) -> None:
        self._sale_repo = sale_repo
        self._item_repo = item_repo

    def execute(self, sale_id: int, company_id: int | None = None) -> SaleStateOutput:
        sale = self._sale_repo.get_by_id(sale_id, company_id=company_id)
        if sale is None:
            raise NotFound(f"Venda {sale_id} não encontrada.")
        items = self._item_repo.list_by_sale(sale_id)
        item_views = tuple(
            SaleItemView(
                item_id=item.id or 0,
                description=item.description,
                quantity_thousandths=item.quantity_thousandths,
                unit=item.unit,
                unit_price_cents=item.unit_price_cents,
                line_total_cents=item.line_total_cents,
                cancelled=item.cancelled,
            )
            for item in items
        )
        return SaleStateOutput(
            sale_id=sale.id or 0,
            status=sale.status,
            subtotal_cents=sale.subtotal_cents,
            discount_cents=sale.discount_cents,
            total_cents=sale.total_cents,
            items=item_views,
        )
