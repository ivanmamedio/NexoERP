"""Cancel receivable use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.treasury.application.ports import ReceivableRepository
from erp.shared.domain.errors import NotFound


@dataclass(slots=True, frozen=True)
class CancelReceivableInput:
    receivable_id: int


class CancelReceivable:
    def __init__(self, receivable_repo: ReceivableRepository) -> None:
        self._receivable_repo = receivable_repo

    def execute(self, input_data: CancelReceivableInput) -> None:
        receivable = self._receivable_repo.get_by_id(input_data.receivable_id)
        if receivable is None:
            raise NotFound(f"Receivable {input_data.receivable_id} not found")
        receivable.cancel()
        self._receivable_repo.save(receivable)
