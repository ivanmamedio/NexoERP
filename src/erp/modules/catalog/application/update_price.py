"""Update price use case — requires product.price.update permission and emits audit event."""

from __future__ import annotations

from erp.modules.catalog.application.ports import ProductRepository
from erp.modules.catalog.domain.product import Product
from erp.shared.application.events import EventBus
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError
from erp.shared.domain.events import EntityUpdated


class UpdatePriceInput:
    def __init__(
        self,
        *,
        product_id: int,
        new_price_cents: int,
        user_id: int | None,
        username: str,
        reason: str = "",
        company_id: int | None = None,
    ) -> None:
        self.product_id = product_id
        self.new_price_cents = new_price_cents
        self.user_id = user_id
        self.username = username
        self.reason = reason
        self.company_id = company_id


class UpdatePriceOutput:
    def __init__(self, product: Product, old_price_cents: int) -> None:
        self.product = product
        self.old_price_cents = old_price_cents


class UpdatePrice:
    def __init__(
        self,
        repository: ProductRepository,
        event_bus: EventBus,
        user_permissions: set[str],
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus
        self._user_permissions = user_permissions

    def execute(self, input: UpdatePriceInput) -> UpdatePriceOutput:
        if "product.price.update" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para alterar preços (product.price.update)."
            )

        product = self._repository.get_by_id(input.product_id)
        if product is None:
            raise NotFound(f"Produto {input.product_id} não encontrado.")
        if product.company_id != input.company_id:
            raise ValidationError("Produto pertence a outra empresa.")

        old_price_cents = product.price_cents
        product.price_cents = input.new_price_cents
        self._repository.save(product)

        self._event_bus.publish(
            EntityUpdated(
                entity_type="Product",
                entity_id=product.id,
                user_id=input.user_id,
                username=input.username,
                before={"price_cents": old_price_cents},
                after={"price_cents": input.new_price_cents},
            )
        )
        return UpdatePriceOutput(product=product, old_price_cents=old_price_cents)
