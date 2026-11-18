"""Update credit customer use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.credit_notebook.application.ports import CreditCustomerRepository
from erp.modules.credit_notebook.domain.credit_customer import CreditCustomer
from erp.shared.domain.errors import NotFound, ValidationError


@dataclass(slots=True, frozen=True)
class UpdateCreditCustomerInput:
    customer_id: int
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None
    credit_limit_cents: int | None = None
    status: str | None = None
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class UpdateCreditCustomerOutput:
    customer_id: int


class UpdateCreditCustomer:
    def __init__(self, repository: CreditCustomerRepository) -> None:
        self._repository = repository

    def execute(self, input_data: UpdateCreditCustomerInput) -> UpdateCreditCustomerOutput:
        customer = self._repository.get_by_id(input_data.customer_id)
        if customer is None:
            raise NotFound(f"Cliente {input_data.customer_id} não encontrado")

        if input_data.name is not None:
            if not input_data.name.strip():
                raise ValidationError("Nome não pode ser vazio")
            customer.name = input_data.name.strip()

        if input_data.phone is not None:
            if not input_data.phone.strip():
                raise ValidationError("Telefone não pode ser vazio")
            # Check if phone already exists for another customer
            existing = self._repository.get_by_phone(
                input_data.phone, input_data.company_id
            )
            if existing and existing.id != input_data.customer_id:
                raise ValidationError(f"Telefone já cadastrado para: {existing.name}")
            customer.phone = input_data.phone.strip()

        if input_data.email is not None:
            customer.email = input_data.email.strip().lower() if input_data.email else ""

        if input_data.address is not None:
            customer.address = input_data.address.strip() if input_data.address else ""

        if input_data.notes is not None:
            customer.notes = input_data.notes.strip() if input_data.notes else ""

        if input_data.credit_limit_cents is not None:
            customer.credit_limit_cents = max(0, input_data.credit_limit_cents)

        if input_data.status is not None:
            if input_data.status not in ("active", "blocked", "inactive"):
                raise ValidationError("Status inválido")
            customer.status = input_data.status

        customer.updated_at = customer.__dataclass_fields__["updated_at"].default_factory()  # type: ignore
        # Actually just use datetime.now(UTC)
        from datetime import UTC, datetime
        customer.updated_at = datetime.now(UTC)

        self._repository.save(customer)
        return UpdateCreditCustomerOutput(customer_id=customer.id or 0)