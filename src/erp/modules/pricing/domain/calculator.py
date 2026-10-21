"""Pricing calculation service — pure domain logic."""

from __future__ import annotations

from dataclasses import dataclass

from erp.shared.domain.errors import ValidationError


class PricingMode:
    """Modo de cálculo da taxa de desconto sobre o preço."""

    WEIGHTED_AVERAGE = "weighted_average"
    WORST_CASE = "worst_case"


@dataclass(frozen=True, slots=True)
class PricingInput:
    """Dados de entrada para o cálculo de preço de venda."""

    cost_cents: int
    tax_pct_hundredths: int  # ex: 6% = 600
    card_fee_pct_hundredths: int  # ex: 3% = 300
    margin_pct_hundredths: int  # ex: 30% = 3000
    mode: str = PricingMode.WEIGHTED_AVERAGE


@dataclass(frozen=True, slots=True)
class PricingOutput:
    """Resultado do cálculo de preço."""

    sale_price_cents: int
    cost_cents: int
    tax_amount_cents: int
    card_fee_amount_cents: int
    margin_amount_cents: int
    net_margin_pct_hundredths: int  # margem líquida real em centesimos
    mode: str


class PriceCalculator:
    """Calcula preço de venda com base em custo, impostos, taxa de cartão e margem.

    Fórmula:
        preço = (custo + custos_fixos) / (1 - (imposto% + taxa_cartão% + margem%))

    Quando o denominador <= 0, levanta ValidationError porque o preço seria
    infinito ou negativo (margem + impostos >= 100%).
    """

    def calculate(self, input: PricingInput) -> PricingOutput:
        if input.cost_cents < 0:
            raise ValidationError("Custo não pode ser negativo.")

        tax_rate = input.tax_pct_hundredths / 10000.0
        card_rate = input.card_fee_pct_hundredths / 10000.0
        margin_rate = input.margin_pct_hundredths / 10000.0

        total_rate = tax_rate + card_rate + margin_rate
        denominator = 1.0 - total_rate

        if denominator <= 0:
            raise ValidationError(
                "Denominador invalido: imposto + taxa cartao + margem deve ser menor que 100% "
                f"(atual: {total_rate * 100:.2f}%)."
            )

        # Modo pior caso: considera a maior taxa entre imposto e cartao
        if input.mode == PricingMode.WORST_CASE:
            worst_rate = max(tax_rate, card_rate)
            denominator = 1.0 - (worst_rate + margin_rate)
            if denominator <= 0:
                raise ValidationError(
                    "Denominador invalido no modo pior caso: taxa maxima + margem >= 100%."
                )

        sale_price = input.cost_cents / denominator
        sale_price_cents = int(sale_price + 0.5)  # arredondamento para centavo mais proximo

        # Valores reais sobre o preço calculado
        tax_amount_cents = int(sale_price_cents * tax_rate + 0.5)
        card_fee_amount_cents = int(sale_price_cents * card_rate + 0.5)
        margin_amount_cents = int(sale_price_cents * margin_rate + 0.5)

        # Margem líquida real = (preço - custo - impostos - taxas) / preço
        net_amount = sale_price_cents - input.cost_cents - tax_amount_cents - card_fee_amount_cents
        net_margin_pct_hundredths = (
            int((net_amount / sale_price_cents) * 10000) if sale_price_cents else 0
        )

        return PricingOutput(
            sale_price_cents=sale_price_cents,
            cost_cents=input.cost_cents,
            tax_amount_cents=tax_amount_cents,
            card_fee_amount_cents=card_fee_amount_cents,
            margin_amount_cents=margin_amount_cents,
            net_margin_pct_hundredths=net_margin_pct_hundredths,
            mode=input.mode,
        )
