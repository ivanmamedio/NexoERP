"""Finalize sale use case — payment validation, change, stock."""

from __future__ import annotations

from erp.modules.sales.application.ports import (
    ProductCatalogPort,
    SaleItemRepository,
    SalePaymentRepository,
    SaleRepository,
)
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_payment import PaymentMethod, SalePayment
from erp.shared.domain.errors import NotFound, ValidationError


class FinalizePaymentInput:
    def __init__(self, *, method: str, amount_cents: int) -> None:
        self.method = method
        self.amount_cents = amount_cents


class FinalizeSaleInput:
    def __init__(
        self,
        *,
        sale_id: int,
        payments: list[FinalizePaymentInput],
        user_id: int | None,
        username: str,
        session_id: int | None = None,
        company_id: int | None = None,
    ) -> None:
        self.sale_id = sale_id
        self.payments = payments
        self.user_id = user_id
        self.username = username
        self.session_id = session_id
        self.company_id = company_id


class FinalizeSaleOutput:
    def __init__(self, sale: Sale, change_cents: int) -> None:
        self.sale = sale
        self.change_cents = change_cents


class FinalizeSale:
    """Finaliza venda: pagamento, estoque, registros."""

    def __init__(
        self,
        sale_repo: SaleRepository,
        item_repo: SaleItemRepository,
        payment_repo: SalePaymentRepository,
        product_repo: ProductCatalogPort,
    ) -> None:
        self._sale_repo = sale_repo
        self._item_repo = item_repo
        self._payment_repo = payment_repo
        self._product_repo = product_repo

    def execute(self, input: FinalizeSaleInput) -> FinalizeSaleOutput:
        sale = self._sale_repo.get_by_id(input.sale_id)
        if sale is None:
            raise NotFound(f"Venda {input.sale_id} não encontrada.")
        if not sale.is_draft():
            raise ValidationError("Venda não está mais aberta.")

        items = [i for i in self._item_repo.list_by_sale(sale.id or 0) if not i.cancelled]
        if not items:
            raise ValidationError("Venda não possui itens.")

        # Valida pagamentos
        total_paid = 0
        cash_paid = 0
        for p in input.payments:
            if p.amount_cents <= 0:
                raise ValidationError("Valor de pagamento deve ser positivo.")
            if p.method not in (PaymentMethod.CASH, PaymentMethod.PIX, PaymentMethod.CARD):
                raise ValidationError(f"Meio de pagamento '{p.method}' inválido.")
            total_paid += p.amount_cents
            if p.method == PaymentMethod.CASH:
                cash_paid += p.amount_cents

        if total_paid < sale.total_cents:
            raise ValidationError(
                f"Pagamento insuficiente: R$ {total_paid / 100:.2f} "
                f"< R$ {sale.total_cents / 100:.2f}."
            )

        change = total_paid - sale.total_cents
        # Troco só vem de pagamento em dinheiro
        if change > 0 and cash_paid < change:
            raise ValidationError("Troco disponível apenas de pagamento em dinheiro.")

        # Baixa estoque (atômico: falha aqui desfaz tudo via UoW)
        for item in items:
            if item.product_id is None:
                continue
            product = self._product_repo.get_by_id(item.product_id)
            if product is None:
                raise NotFound(f"Produto {item.product_id} não encontrado.")
            new_qty = product.stock_qty - item.quantity_thousandths
            if new_qty < 0:
                raise ValidationError(f"Estoque insuficiente de '{product.name}' no fechamento.")
            product.stock_qty = new_qty
            self._product_repo.save(product)

        # Registra pagamentos
        remaining_change = change
        for p in input.payments:
            payment_change = 0
            if p.method == PaymentMethod.CASH and remaining_change > 0:
                payment_change = min(remaining_change, p.amount_cents)
                remaining_change -= payment_change
            payment = SalePayment(
                sale_id=sale.id or 0,
                company_id=sale.company_id,
                method=p.method,
                amount_cents=p.amount_cents,
                change_cents=payment_change,
            )
            self._payment_repo.add(payment)

        sale.finalize(paid_cents=total_paid, change_cents=change)
        if input.session_id is not None:
            sale.session_id = input.session_id
        self._sale_repo.save(sale)

        return FinalizeSaleOutput(sale=sale, change_cents=change)
