"""Create credit entry use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from erp.modules.credit_notebook.application.ports import (
    CreditCustomerRepository,
    CreditEntryRepository,
)
from erp.modules.credit_notebook.domain.credit_entry import (
    CreditEntry,
    CreditEntryStatus,
    CreditEntryType,
)
from erp.shared.domain.errors import NotFound, ValidationError


@dataclass(slots=True, frozen=True)
class CreateCreditEntryInput:
    customer_id: int
    company_id: int | None
    entry_type: str  # charge, payment, adjustment, interest
    description: str
    amount_cents: int
    due_date: datetime | None = None
    reference_type: str = ""
    reference_id: int | None = None
    notes: str = ""
    created_by_user_id: int | None = None
    created_by_username: str = ""


@dataclass(slots=True, frozen=True)
class CreateCreditEntryOutput:
    entry_id: int


class CreateCreditEntry:
    def __init__(
        self,
        customer_repo: CreditCustomerRepository,
        entry_repo: CreditEntryRepository,
    ) -> None:
        self._customer_repo = customer_repo
        self._entry_repo = entry_repo

    def execute(self, input_data: CreateCreditEntryInput) -> CreateCreditEntryOutput:
        # Validate customer
        customer = self._customer_repo.get_by_id(input_data.customer_id)
        if customer is None:
            raise NotFound(f"Cliente {input_data.customer_id} não encontrado")

        if customer.company_id != input_data.company_id:
            raise ValidationError("Cliente não pertence a esta empresa")

        if input_data.entry_type not in (
            CreditEntryType.CHARGE,
            CreditEntryType.PAYMENT,
            CreditEntryType.ADJUSTMENT,
            CreditEntryType.INTEREST,
        ):
            raise ValidationError("Tipo de lançamento inválido")

        if not input_data.description or not input_data.description.strip():
            raise ValidationError("Descrição é obrigatória")

        if input_data.amount_cents <= 0:
            raise ValidationError("Valor deve ser maior que zero")

        # Validate credit limit for charges
        if input_data.entry_type == CreditEntryType.CHARGE:
            if customer.is_over_limit:
                raise ValidationError(
                    f"Cliente excede o limite de crédito. "
                    f"Saldo: R$ {customer.current_balance_cents / 100:.2f}, "
                    f"Limite: R$ {customer.credit_limit_cents / 100:.2f}"
                )

            # Check if this charge would exceed limit
            if customer.credit_limit_cents > 0:
                new_balance = customer.current_balance_cents + input_data.amount_cents
                if new_balance > customer.credit_limit_cents:
                    raise ValidationError(
                        f"Este lançamento excederia o limite de crédito. "
                        f"Disponível: R$ {customer.available_credit_cents / 100:.2f}"
                    )

        entry = CreditEntry(
            customer_id=input_data.customer_id,
            company_id=input_data.company_id,
            entry_type=input_data.entry_type,
            description=input_data.description.strip(),
            amount_cents=input_data.amount_cents,
            status=CreditEntryStatus.PENDING,
            due_date=input_data.due_date,
            reference_type=input_data.reference_type,
            reference_id=input_data.reference_id,
            notes=input_data.notes.strip() if input_data.notes else "",
            created_by_user_id=input_data.created_by_user_id,
            created_by_username=input_data.created_by_username,
        )

        self._entry_repo.add(entry)
        return CreateCreditEntryOutput(entry_id=entry.id or 0)
