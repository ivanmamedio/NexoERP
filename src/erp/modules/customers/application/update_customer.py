"""UpdateCustomer use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.customers.application.ports import CustomerRepository
from erp.modules.customers.domain.customer import Customer  # noqa: F401
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError


@dataclass(slots=True, frozen=True)
class UpdateCustomerInput:
    customer_id: int
    name: str | None = None
    phone: str | None = None
    document: str | None = None
    credit_limit_cents: int | None = None
    is_active: bool | None = None
    user_id: int | None = None
    username: str = ""
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class UpdateCustomerOutput:
    customer_id: int
    name: str


class UpdateCustomer:
    """Atualiza um cliente existente. Exige permissão customer.update."""

    def __init__(
        self,
        repo: CustomerRepository,
        user_permissions: set[str],
    ) -> None:
        self._repo = repo
        self._user_permissions = user_permissions

    def execute(self, input: UpdateCustomerInput) -> UpdateCustomerOutput:
        if "customer.update" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para atualizar clientes (customer.update)."
            )

        customer = self._repo.get_by_id(input.customer_id)
        if customer is None:
            raise NotFound(f"Cliente {input.customer_id} não encontrado.")

        if customer.company_id != input.company_id:
            raise PermissionDenied("Cliente não pertence à empresa da sessão.")

        if input.name is not None:
            if not input.name.strip():
                raise ValidationError("Nome do cliente é obrigatório.")
            customer.name = input.name.strip()
        if input.phone is not None:
            customer.phone = input.phone.strip()
        if input.document is not None:
            customer.document = input.document
        if input.credit_limit_cents is not None:
            customer.credit_limit_cents = input.credit_limit_cents
        if input.is_active is not None:
            customer.is_active = input.is_active

        self._repo.save(customer)

        return UpdateCustomerOutput(
            customer_id=customer.id or 0,
            name=customer.name,
        )
