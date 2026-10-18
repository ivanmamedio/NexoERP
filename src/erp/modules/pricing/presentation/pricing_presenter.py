"""Pricing assistant presenter (domain- and application-layer only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.pricing.application.calculate_price import (
    CalculatePriceInput,
    CalculatePriceOutput,
)
from erp.modules.pricing.application.services import PricingServices
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import ValidationError


@runtime_checkable
class PricingView(Protocol):
    """Contract for the pricing assistant screen."""

    def show_result(self, output: CalculatePriceOutput) -> None: ...
    def show_error(self, message: str) -> None: ...
    def get_product_id(self) -> int | None: ...


class PricingPresenter:
    """Orquestra o assistente de precificacao sem depender de Qt."""

    def __init__(
        self,
        view: PricingView,
        services: PricingServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def calculate(
        self,
        *,
        cost_cents: int,
        tax_pct_hundredths: int,
        card_fee_pct_hundredths: int,
        margin_pct_hundredths: int,
    ) -> None:
        try:
            output = self._services.calculate_price(
                CalculatePriceInput(
                    cost_cents=cost_cents,
                    tax_pct_hundredths=tax_pct_hundredths,
                    card_fee_pct_hundredths=card_fee_pct_hundredths,
                    margin_pct_hundredths=margin_pct_hundredths,
                )
            )
            self._view.show_result(output)
        except ValidationError as exc:
            self._view.show_error(str(exc))

    def apply_to_product(
        self,
        *,
        new_price_cents: int,
        user_id: int | None,
        username: str,
        reason: str = "",
    ) -> bool:
        product_id = self._view.get_product_id()
        if product_id is None:
            self._view.show_error("Nenhum produto selecionado.")
            return False
        try:
            self._services.apply_to_product(
                product_id=product_id,
                new_price_cents=new_price_cents,
                user_id=user_id,
                username=username,
                reason=reason,
                company_id=self._session.company_id,
            )
            return True
        except ValidationError as exc:
            self._view.show_error(str(exc))
            return False
