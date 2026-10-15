from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal


@dataclass(frozen=True)
class Money:
    cents: int

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.cents + other.cents)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.cents - other.cents)

    def __mul__(self, other: int) -> Money:
        if not isinstance(other, int):
            return NotImplemented
        return Money(self.cents * other)

    def multiply_by_qty(self, quantity_thousandths: int) -> Money:
        """Multiplica por quantidade fracionada (em milesimos)."""
        d_cents = Decimal(self.cents)
        d_qty = Decimal(quantity_thousandths) / Decimal(1000)
        result = (d_cents * d_qty).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        return Money(int(result))

    def multiply_by_pct(self, pct_hundredths: int) -> Money:
        """Multiplica por percentual (em centesimos, ex: 6% = 600)."""
        d_cents = Decimal(self.cents)
        d_pct = Decimal(pct_hundredths) / Decimal(10000)
        result = (d_cents * d_pct).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        return Money(int(result))

    def format_brl(self) -> str:
        is_negative = self.cents < 0
        abs_cents = abs(self.cents)
        reais = abs_cents // 100
        centavos = abs_cents % 100
        reais_str = f"{reais:,}".replace(",", ".")
        sign = "-" if is_negative else ""
        return f"{sign}R$ {reais_str},{centavos:02d}"


@dataclass(frozen=True)
class Quantity:
    thousandths: int

    def __add__(self, other: Quantity) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return Quantity(self.thousandths + other.thousandths)

    def __sub__(self, other: Quantity) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return Quantity(self.thousandths - other.thousandths)
