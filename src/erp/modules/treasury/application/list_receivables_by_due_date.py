"""List receivables by due date range use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from erp.modules.treasury.application.ports import ReceivableRepository


@runtime_checkable
class ReceivableView(Protocol):
    receivable_id: int
    customer_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    due_date: datetime | None
    received_amount_cents: int
    pending_amount_cents: int


@dataclass(slots=True, frozen=True)
class ReceivableViewImpl:
    receivable_id: int
    customer_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    due_date: datetime | None
    received_amount_cents: int
    pending_amount_cents: int


@dataclass(slots=True, frozen=True)
class ListReceivablesByDueDateInput:
    start_date: datetime
    end_date: datetime
    company_id: int | None = None
    status: str | None = None


@dataclass(slots=True, frozen=True)
class ListReceivablesByDueDateOutput:
    receivables: tuple[ReceivableViewImpl, ...]


class ListReceivablesByDueDate:
    """Lista contas a receber com vencimento no intervalo especificado."""

    def __init__(self, repo: ReceivableRepository) -> None:
        self._repo = repo

    def execute(self, input_data: ListReceivablesByDueDateInput) -> ListReceivablesByDueDateOutput:
        receivables = self._repo.list_by_due_date_range(
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            company_id=input_data.company_id,
            status=input_data.status,
        )
        views = tuple(
            ReceivableViewImpl(
                receivable_id=r.id or 0,
                customer_id=r.customer_id,
                category_id=r.category_id,
                description=r.description,
                total_amount_cents=r.total_amount_cents,
                status=r.status,
                issue_date=r.issue_date,
                due_date=r.due_date,
                received_amount_cents=r.received_amount_cents,
                pending_amount_cents=r.pending_amount_cents,
            )
            for r in receivables
        )
        return ListReceivablesByDueDateOutput(receivables=views)