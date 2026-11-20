"""Create credit customer use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.credit_notebook.application.ports import CreditCustomerRepository
from erp.modules.credit_notebook.domain.credit_customer import CreditCustomer
from erp.shared.domain.errors import ValidationError


@dataclass(slots=True, frozen=True)
class CreateCreditCustomerInput:
    name: str
    phone: str
    email: str = ""
    address: str = ""
    notes: str = ""
    credit_limit_cents: int = 0
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class CreateCreditCustomerOutput:
    customer_id: int


class CreateCreditCustomer:
    def __init__(self, repository: CreditCustomerRepository) -> None:
        self._repository = repository

    def execute(self, input_data: CreateCreditCustomerInput) -> CreateCreditCustomerOutput:
        if not input_data.name or not input_data.name.strip():
            raise ValidationError("Nome do cliente é obrigatório")
        if not input_data.phone or not input_data.phone.strip():
            raise ValidationError("Telefone é obrigatório")

        # Check if phone already exists for this company
        existing = self._repository.get_by_phone(input_data.phone, input_data.company_id)
        if existing:
            raise ValidationError(f"Já existe cliente com este telefone: {existing.name}")

        customer = CreditCustomer(
            company_id=input_data.company_id,
            name=input_data.name.strip(),
            phone=input_data.phone.strip(),
            email=input_data.email.strip().lower() if input_data.email else "",
            address=input_data.address.strip() if input_data.address else "",
            notes=input_data.notes.strip() if input_data.notes else "",
            credit_limit_cents=input_data.credit_limit_cents,
            status="active",
        )

        self._repository.add(customer)
        return CreateCreditCustomerOutput(customer_id=customer.id or 0)
