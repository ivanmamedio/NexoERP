"""Receive receivable use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from erp.modules.treasury.application.ports import ReceivableRepository
from erp.shared.domain.errors import NotFound


@dataclass(slots=True, frozen=True)
class ReceiveReceivableInput:
    receivable_id: int
    amount_cents: int
    received_at: datetime | None = None


class ReceiveReceivable:
    def __init__(self, receivable_repo: ReceivableRepository) -> None:
        self._receivable_repo = receivable_repo

    def execute(self, input_data: ReceiveReceivableInput) -> None:
        receivable = self._receivable_repo.get_by_id(input_data.receivable_id)
        if receivable is None:
            raise NotFound(f"Receivable {input_data.receivable_id} not found")
        receivable.receive(input_data.amount_cents, input_data.received_at)
        self._receivable_repo.save(receivable)