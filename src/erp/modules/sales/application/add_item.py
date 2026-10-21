"""Add item use case — resolves product by barcode/SKU/name, snapshots price."""

from __future__ import annotations

from erp.modules.sales.application.ports import (
    ProductCatalogPort,
    SaleItemRepository,
    SaleRepository,
)
from erp.modules.sales.domain.sale_item import SaleItem
from erp.shared.domain.errors import NotFound, ValidationError


class AddItemInput:
    def __init__(
        self,
        *,
        sale_id: int,
        query: str,
        quantity_thousandths: int = 1000,
        company_id: int | None = None,
    ) -> None:
        self.sale_id = sale_id
        self.query = query
        self.quantity_thousandths = quantity_thousandths
        self.company_id = company_id


class AddItemOutput:
    def __init__(self, item: SaleItem, sale_total_cents: int) -> None:
        self.item = item
        self.sale_total_cents = sale_total_cents


class AddItem:
    """Adiciona item à venda buscando produto por SKU/nome."""

    def __init__(
        self,
        sale_repo: SaleRepository,
        item_repo: SaleItemRepository,
        product_repo: ProductCatalogPort,
    ) -> None:
        self._sale_repo = sale_repo
        self._item_repo = item_repo
        self._product_repo = product_repo

    def execute(self, input: AddItemInput) -> AddItemOutput:
        sale = self._sale_repo.get_by_id(input.sale_id)
        if sale is None:
            raise NotFound(f"Venda {input.sale_id} não encontrada.")
        if not sale.is_draft():
            raise ValidationError("Venda não está mais aberta.")

        if input.quantity_thousandths <= 0:
            raise ValidationError("Quantidade deve ser positiva.")

        # Multiplicador "3*CODIGO"
        query = input.query.strip()
        multiplier = 1
        if "*" in query:
            parts = query.split("*", 1)
            if parts[0].strip().isdigit():
                multiplier = int(parts[0].strip())
                query = parts[1].strip()

        company_id = input.company_id or sale.company_id
        # Busca por SKU exato
        product = self._product_repo.get_by_sku(query, company_id)
        if product is None:
            # Busca por nome no banco (índice), prefixo primeiro; substring como fallback
            candidates = self._product_repo.search(query, company_id, limit=1)
            if not candidates:
                raise NotFound(f"Produto '{query}' não encontrado.")
            product = candidates[0]

        if not product.active:
            raise ValidationError(f"Produto '{product.name}' está inativo.")

        qty = input.quantity_thousandths * multiplier
        if product.stock_qty < qty:
            raise ValidationError(
                f"Estoque insuficiente de '{product.name}' "
                f"({product.stock_qty / 1000:.3f} {product.unit} disponível)."
            )

        item = SaleItem(
            sale_id=sale.id or 0,
            company_id=sale.company_id,
            product_id=product.id,
            description=product.name,
            unit_price_cents=product.price_cents,
            quantity_thousandths=qty,
            unit=product.unit,
        )
        item.line_total_cents = item.compute_line_total()
        self._item_repo.add(item)

        # Recalcula subtotal da venda (item já foi persistido acima)
        items = self._item_repo.list_by_sale(sale.id or 0)
        subtotal = sum(i.line_total_cents for i in items if not i.cancelled)
        sale.recalculate(subtotal)
        self._sale_repo.save(sale)

        return AddItemOutput(item=item, sale_total_cents=sale.total_cents)
