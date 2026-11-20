"""Cancel payable use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.treasury.application.ports import PayableRepository
from erp.shared.domain.errors import NotFound


@dataclass(slots=True, frozen=True)
class CancelPayableInput:
    payable_id: int


class CancelPayable:
    def __init__(self, payable_repo: PayableRepository) -> None:
        self._payable_repo = payable_repo

    def execute(self, input_data: CancelPayableInput) -> None:
        payable = self._payable_repo.get_by_id(input_data.payable_id)
        if payable is None:
            raise NotFound(f"Payable {input_data.payable_id} not found")
        payable.cancel()
        self._payable_repo.save(payable)
