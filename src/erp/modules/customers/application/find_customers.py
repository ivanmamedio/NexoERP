"""Customer query use cases (consulta por nome/telefone)."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.customers.application.ports import CustomerRepository
from erp.shared.domain.errors import PermissionDenied


@dataclass(slots=True, frozen=True)
class FindCustomersInput:
    company_id: int
    name_contains: str | None = None
    phone: str | None = None


@dataclass(slots=True, frozen=True)
class CustomerView:
    customer_id: int
    name: str
    phone: str
    document: str | None
    credit_limit_cents: int
    is_active: bool


class FindCustomers:
    """Consulta clientes por nome ou telefone. Exige customer.read."""

    def __init__(
        self,
        repo: CustomerRepository,
        user_permissions: set[str],
    ) -> None:
        self._repo = repo
        self._user_permissions = user_permissions

    def execute(self, input: FindCustomersInput) -> list[CustomerView]:
        if "customer.read" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para consultar clientes (customer.read)."
            )

        customers = self._repo.list_by_company(
            company_id=input.company_id,
            name_contains=input.name_contains,
        )

        result = []
        for c in customers:
            if input.phone is not None and c.phone != input.phone:
                continue
            result.append(
                CustomerView(
                    customer_id=c.id or 0,
                    name=c.name,
                    phone=c.phone,
                    document=c.document,
                    credit_limit_cents=c.credit_limit_cents,
                    is_active=c.is_active,
                )
            )
        return result
