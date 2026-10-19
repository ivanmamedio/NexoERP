"""Unit tests for the pricing calculator."""

from __future__ import annotations

import pytest

from erp.modules.pricing.domain.calculator import (
    PriceCalculator,
    PricingInput,
)
from erp.shared.domain.errors import ValidationError


def test_calculator_example_from_task() -> None:
    """custo 10,00 / imposto 6% / cartao 3% / margem 30% = R$ 16,39."""
    calc = PriceCalculator()
    output = calc.calculate(
        PricingInput(
            cost_cents=1000,
            tax_pct_hundredths=600,
            card_fee_pct_hundredths=300,
            margin_pct_hundredths=3000,
        )
    )
    assert output.sale_price_cents == 1639
    assert output.mode == "weighted_average"


def test_calculator_denominator_zero_or_negative() -> None:
    """imposto + taxa + margem >= 100% deve levantar ValidationError."""
    calc = PriceCalculator()
    with pytest.raises(ValidationError, match="Denominador invalido"):
        calc.calculate(
            PricingInput(
                cost_cents=1000,
                tax_pct_hundredths=5000,  # 50%
                card_fee_pct_hundredths=3000,  # 30%
                margin_pct_hundredths=3000,  # 30%
            )
        )


def test_calculator_worst_case_mode() -> None:
    calc = PriceCalculator()
    output = calc.calculate(
        PricingInput(
            cost_cents=1000,
            tax_pct_hundredths=600,
            card_fee_pct_hundredths=300,
            margin_pct_hundredths=3000,
            mode="worst_case",
        )
    )
    assert output.mode == "worst_case"
    assert output.sale_price_cents > 0


def test_calculator_negative_cost() -> None:
    calc = PriceCalculator()
    with pytest.raises(ValidationError, match="Custo"):
        calc.calculate(
            PricingInput(
                cost_cents=-100,
                tax_pct_hundredths=600,
                card_fee_pct_hundredths=300,
                margin_pct_hundredths=3000,
            )
        )
