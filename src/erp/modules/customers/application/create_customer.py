"""CreateCustomer use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.customers.application.ports import CustomerRepository
from erp.modules.customers.domain.customer import Customer
from erp.shared.domain.errors import PermissionDenied, ValidationError


@dataclass(slots=True, frozen=True)
class CreateCustomerInput:
    name: str
    phone: str = ""
    document: str | None = None
    credit_limit_cents: int = 0
    user_id: int | None = None
    username: str = ""
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class CreateCustomerOutput:
    customer_id: int
    name: str


class CreateCustomer:
    """Cria um novo cliente. Exige permissão customer.create."""

    def __init__(
        self,
        repo: CustomerRepository,
        user_permissions: set[str],
    ) -> None:
        self._repo = repo
        self._user_permissions = user_permissions

    def execute(self, input: CreateCustomerInput) -> CreateCustomerOutput:
        if "customer.create" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para criar clientes (customer.create)."
            )

        if not input.name.strip():
            raise ValidationError("Nome do cliente é obrigatório.")

        customer = Customer(
            company_id=input.company_id or 0,
            name=input.name.strip(),
            phone=input.phone.strip(),
            document=input.document,
            credit_limit_cents=input.credit_limit_cents,
            is_active=True,
        )
        self._repo.add(customer)

        return CreateCustomerOutput(
            customer_id=customer.id or 0,
            name=customer.name,
        )
