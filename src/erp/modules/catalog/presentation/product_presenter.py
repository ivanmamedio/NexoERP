"""Catalog product presenter (domain- and application-layer only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.catalog.application.create_product import CreateProductInput
from erp.modules.catalog.application.services import CatalogServices
from erp.modules.catalog.application.update_price import UpdatePriceInput
from erp.modules.catalog.domain.product import Product
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound, PermissionDenied


@runtime_checkable
class ProductListView(Protocol):
    """Contract for the product list screen."""

    def set_products(self, products: list[Product]) -> None: ...
    def show_error(self, message: str) -> None: ...


class ProductListPresenter:
    """Orquestra a listagem de produtos sem depender de Qt."""

    def __init__(
        self,
        view: ProductListView,
        services: CatalogServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def load(self) -> None:
        try:
            output = self._services.list_low_stock(company_id=self._session.company_id)
            self._view.set_products(output.products)
        except NotFound as exc:
            self._view.show_error(str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            self._view.show_error(str(exc))


@runtime_checkable
class ProductEditView(Protocol):
    """Contract for the product create/edit screen."""

    def show_error(self, message: str) -> None: ...
    def accept(self) -> None: ...
    def load_product(self, product: Product | None) -> None: ...


class ProductEditPresenter:
    """Orquestra o cadastro/edição de produtos sem depender de Qt."""

    def __init__(
        self,
        view: ProductEditView,
        services: CatalogServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def save(
        self,
        *,
        sku: str,
        name: str,
        description: str,
        unit: str,
        cost_cents: int,
        margin_pct: int,
        price_cents: int,
        min_stock_qty: int,
        stock_qty: int,
        sold_by_weight: bool,
        active: bool,
    ) -> bool:
        if not sku:
            self._view.show_error("Informe o SKU.")
            return False
        if not name:
            self._view.show_error("Informe o nome do produto.")
            return False

        try:
            self._services.create_product(
                CreateProductInput(
                    sku=sku,
                    name=name,
                    description=description,
                    unit=unit,
                    cost_cents=cost_cents,
                    margin_pct=margin_pct,
                    price_cents=price_cents,
                    min_stock_qty=min_stock_qty,
                    stock_qty=stock_qty,
                    sold_by_weight=sold_by_weight,
                    active=active,
                    company_id=self._session.company_id,
                )
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._view.show_error(str(exc))
            return False

        self._view.accept()
        return True

    def update_price(
        self,
        *,
        product_id: int,
        new_price_cents: int,
        user_id: int | None,
        username: str,
        reason: str = "",
    ) -> bool:
        try:
            self._services.update_price(
                UpdatePriceInput(
                    product_id=product_id,
                    new_price_cents=new_price_cents,
                    user_id=user_id,
                    username=username,
                    reason=reason,
                    company_id=self._session.company_id,
                )
            )
        except PermissionDenied as exc:
            self._view.show_error(str(exc))
            return False
        except NotFound as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:  # pragma: no cover - defensive
            self._view.show_error(str(exc))
            return False
        return True
