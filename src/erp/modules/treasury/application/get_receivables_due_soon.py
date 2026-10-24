"""Get receivables due soon use case (alertas de recebimento)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

from erp.modules.treasury.application.list_receivables_by_due_date import (
    ListReceivablesByDueDate,
    ListReceivablesByDueDateInput,
)
from erp.modules.treasury.application.ports import ReceivableRepository


@runtime_checkable
class ReceivableDueSoonView(Protocol):
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
class ReceivableDueSoonViewImpl:
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
    days_overdue: int  # negativo = vencido, positivo = dias para vencer


@dataclass(slots=True, frozen=True)
class GetReceivablesDueSoonInput:
    days_ahead: int = 7
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class GetReceivablesDueSoonOutput:
    receivables: tuple[ReceivableDueSoonViewImpl, ...]
    total_due_cents: int
    overdue_count: int
    due_soon_count: int


class GetReceivablesDueSoon:
    """Busca contas a receber vencidas ou prestes a vencer (alertas)."""

    def __init__(self, repo: ReceivableRepository) -> None:
        self._list_by_due = ListReceivablesByDueDate(repo)

    def execute(self, input_data: GetReceivablesDueSoonInput) -> GetReceivablesDueSoonOutput:
        now = datetime.now(UTC)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        end_date = end_date + timedelta(days=input_data.days_ahead)

        result = self._list_by_due.execute(
            ListReceivablesByDueDateInput(
                start_date=now,
                end_date=end_date,
                company_id=input_data.company_id,
                status="pending",
            )
        )

        due_soon = []
        overdue_count = 0
        due_soon_count = 0
        total_due = 0

        for r in result.receivables:
            if r.due_date is None:
                continue
            pending = r.pending_amount_cents
            if pending <= 0:
                continue

            days_diff = (r.due_date - now).days

            if days_diff < 0:
                overdue_count += 1
            else:
                due_soon_count += 1

            total_due += pending

            due_soon.append(
                ReceivableDueSoonViewImpl(
                    receivable_id=r.receivable_id,
                    customer_id=r.customer_id,
                    category_id=r.category_id,
                    description=r.description,
                    total_amount_cents=r.total_amount_cents,
                    status=r.status,
                    issue_date=r.issue_date,
                    due_date=r.due_date,
                    received_amount_cents=r.received_amount_cents,
                    pending_amount_cents=r.pending_amount_cents,
                    days_overdue=days_diff,
                )
            )

        # Ordenar: vencidos primeiro (mais antigo), depois por data de vencimento
        due_soon.sort(key=lambda x: (x.days_overdue < 0, x.days_overdue))

        return GetReceivablesDueSoonOutput(
            receivables=tuple(due_soon),
            total_due_cents=total_due,
            overdue_count=overdue_count,
            due_soon_count=due_soon_count,
        )
