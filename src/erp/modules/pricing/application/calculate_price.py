"""Calculate price use case — wraps the pure domain PricingCalculator."""

from __future__ import annotations

from erp.modules.pricing.domain.calculator import (
    PriceCalculator,
    PricingInput,
)


class CalculatePriceInput:
    def __init__(
        self,
        *,
        cost_cents: int,
        tax_pct_hundredths: int,
        card_fee_pct_hundredths: int,
        margin_pct_hundredths: int,
        mode: str = "weighted_average",
        product_id: int | None = None,
    ) -> None:
        self.cost_cents = cost_cents
        self.tax_pct_hundredths = tax_pct_hundredths
        self.card_fee_pct_hundredths = card_fee_pct_hundredths
        self.margin_pct_hundredths = margin_pct_hundredths
        self.mode = mode
        self.product_id = product_id


class CalculatePriceOutput:
    def __init__(
        self,
        *,
        sale_price_cents: int,
        cost_cents: int,
        tax_amount_cents: int,
        card_fee_amount_cents: int,
        margin_amount_cents: int,
        net_margin_pct_hundredths: int,
        mode: str,
    ) -> None:
        self.sale_price_cents = sale_price_cents
        self.cost_cents = cost_cents
        self.tax_amount_cents = tax_amount_cents
        self.card_fee_amount_cents = card_fee_amount_cents
        self.margin_amount_cents = margin_amount_cents
        self.net_margin_pct_hundredths = net_margin_pct_hundredths
        self.mode = mode


class CalculatePrice:
    def __init__(self, calculator: PriceCalculator) -> None:
        self._calculator = calculator

    def execute(self, input: CalculatePriceInput) -> CalculatePriceOutput:
        pricing_input = PricingInput(
            cost_cents=input.cost_cents,
            tax_pct_hundredths=input.tax_pct_hundredths,
            card_fee_pct_hundredths=input.card_fee_pct_hundredths,
            margin_pct_hundredths=input.margin_pct_hundredths,
            mode=input.mode,
        )
        output = self._calculator.calculate(pricing_input)
        return CalculatePriceOutput(
            sale_price_cents=output.sale_price_cents,
            cost_cents=output.cost_cents,
            tax_amount_cents=output.tax_amount_cents,
            card_fee_amount_cents=output.card_fee_amount_cents,
            margin_amount_cents=output.margin_amount_cents,
            net_margin_pct_hundredths=output.net_margin_pct_hundredths,
            mode=output.mode,
        )
