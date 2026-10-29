"""Price updater adapter for catalog module.

Implements the ProductPriceUpdaterPort using the catalog's UpdatePrice use case.
"""

from __future__ import annotations

from collections.abc import Callable

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.application.update_price import UpdatePrice, UpdatePriceInput
from erp.modules.pricing.application.ports import ProductPriceUpdaterPort
from erp.shared.application.events import EventBus


class CatalogPriceUpdater(ProductPriceUpdaterPort):
    """Updates product prices via the catalog's UpdatePrice use case."""

    def __init__(
        self,
        product_repo_factory: Callable[[], ProductRepository],
        event_bus: EventBus,
        user_permissions: set[str],
    ) -> None:
        self._product_repo_factory = product_repo_factory
        self._event_bus = event_bus
        self._user_permissions = user_permissions

    def update_price(
        self,
        *,
        product_id: int,
        new_price_cents: int,
        user_id: int | None,
        username: str,
        reason: str = "",
        company_id: int | None = None,
    ) -> None:
        product_repo = self._product_repo_factory()
        update_price_uc = UpdatePrice(product_repo, self._event_bus, self._user_permissions)
        input_data = UpdatePriceInput(
            product_id=product_id,
            new_price_cents=new_price_cents,
            user_id=user_id,
            username=username,
            reason=reason,
            company_id=company_id,
        )
        update_price_uc.execute(input_data)
