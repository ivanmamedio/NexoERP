"""Application services facade for Pricing."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.catalog.application.services import SqlAlchemyCatalogServices
from erp.modules.catalog.application.update_price import UpdatePriceInput
from erp.modules.pricing.application.calculate_price import (
    CalculatePrice,
    CalculatePriceInput,
    CalculatePriceOutput,
)
from erp.modules.pricing.domain.calculator import PriceCalculator
from erp.shared.domain.errors import ValidationError


class PricingServices:
    """Facade over pricing use cases."""

    def __init__(
        self,
        engine: Engine,
        catalog_services: SqlAlchemyCatalogServices | None = None,
    ) -> None:
        self._engine = engine
        self._calculator = PriceCalculator()
        self._catalog_services = catalog_services

    def calculate_price(self, input: CalculatePriceInput) -> CalculatePriceOutput:
        return CalculatePrice(self._calculator).execute(input)

    def apply_to_product(
        self,
        *,
        product_id: int,
        new_price_cents: int,
        user_id: int | None,
        username: str,
        reason: str = "",
        company_id: int | None = None,
    ) -> None:
        """Aplica o preço calculado a um produto existente (respeita permissão)."""
        if self._catalog_services is None:
            raise ValidationError("Catalogo nao disponivel para aplicar preço.")
        self._catalog_services.update_price(
            UpdatePriceInput(
                product_id=product_id,
                new_price_cents=new_price_cents,
                user_id=user_id,
                username=username,
                reason=reason,
                company_id=company_id,
            )
        )
