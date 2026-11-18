"""Pay payable installment use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from erp.modules.treasury.application.ports import PayableRepository
from erp.shared.domain.errors import NotFound


@dataclass(slots=True, frozen=True)
class PayPayableInput:
    payable_id: int
    installment_number: int
    amount_cents: int
    paid_at: datetime | None = None


class PayPayable:
    def __init__(self, payable_repo: PayableRepository) -> None:
        self._payable_repo = payable_repo

    def execute(self, input_data: PayPayableInput) -> None:
        payable = self._payable_repo.get_by_id(input_data.payable_id)
        if payable is None:
            raise NotFound(f"Payable {input_data.payable_id} not found")
        payable.pay_installment(
            installment_number=input_data.installment_number,
            amount_cents=input_data.amount_cents,
            paid_at=input_data.paid_at,
        )
        self._payable_repo.save(payable)