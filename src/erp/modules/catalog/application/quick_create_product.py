"""Quick create product use case — cadastro rápido de produto direto no PDV.

Permite que o operador cadastre um produto com campos mínimos no meio
da venda, sem sair da tela do PDV, evitando travar o atendimento.
"""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.domain.errors import ValidationError


@dataclass(slots=True, frozen=True)
class QuickCreateProductInput:
    sku: str
    name: str
    price_cents: int
    unit: str = "un"
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class QuickCreateProductOutput:
    product_id: int
    sku: str
    name: str
    price_cents: int


class QuickCreateProduct:
    """Cria um produto rapidamente com campos mínimos.

    Valores padrão: custo=0, margem=0, estoque=0, ativo=True,
    não vendido por peso, sem categoria nem fornecedor.
    """

    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(self, input: QuickCreateProductInput) -> QuickCreateProductOutput:
        if not input.sku:
            raise ValidationError("SKU é obrigatório.")
        if not input.name:
            raise ValidationError("Nome do produto é obrigatório.")
        if input.price_cents < 0:
            raise ValidationError("Preço não pode ser negativo.")

        sku = input.sku.strip().upper()
        name = input.name.strip()

        existing = self._repository.get_by_sku(sku, input.company_id)
        if existing is not None:
            raise ValidationError(f"Já existe produto com SKU {sku} nesta empresa.")

        product = Product(
            sku=sku,
            name=name,
            description="",
            unit=input.unit or "un",
            cost_cents=0,
            margin_pct=0,
            price_cents=input.price_cents,
            min_stock_qty=0,
            stock_qty=0,
            sold_by_weight=False,
            active=True,
            company_id=input.company_id,
        )
        self._repository.add(product)
        return QuickCreateProductOutput(
            product_id=product.id or 0,
            sku=product.sku,
            name=product.name,
            price_cents=product.price_cents,
        )
