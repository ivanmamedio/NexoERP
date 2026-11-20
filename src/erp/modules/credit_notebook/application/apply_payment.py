"""Apply payment to credit entry use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from erp.modules.credit_notebook.application.ports import CreditEntryRepository
from erp.modules.credit_notebook.domain.credit_entry import CreditEntryStatus
from erp.shared.domain.errors import NotFound, ValidationError


@dataclass(slots=True, frozen=True)
class ApplyPaymentInput:
    entry_id: int
    amount_cents: int
    paid_at: datetime | None = None
    company_id: int | None = None


class ApplyPayment:
    def __init__(self, repository: CreditEntryRepository) -> None:
        self._repository = repository

    def execute(self, input_data: ApplyPaymentInput) -> None:
        entry = self._repository.get_by_id(input_data.entry_id)
        if entry is None:
            raise NotFound(f"Lançamento {input_data.entry_id} não encontrado")

        if entry.company_id != input_data.company_id:
            raise ValidationError("Lançamento não pertence a esta empresa")

        if entry.status == CreditEntryStatus.PAID:
            raise ValidationError("Lançamento já quitado")

        if entry.status == CreditEntryStatus.CANCELLED:
            raise ValidationError("Lançamento cancelado")

        if input_data.amount_cents <= 0:
            raise ValidationError("Valor do pagamento deve ser positivo")

        if input_data.amount_cents > entry.pending_amount_cents:
            raise ValidationError("Valor excede o pendente")

        entry.apply_payment(input_data.amount_cents, input_data.paid_at)
        self._repository.save(entry)
