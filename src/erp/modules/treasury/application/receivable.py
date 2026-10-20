"""Receivable application use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from erp.modules.treasury.application.ports import ReceivableRepository
from erp.modules.treasury.domain.receivable import Receivable, ReceivableStatus


class CreateReceivableInput:
    def __init__(
        self,
        *,
        customer_id: int | None,
        category_id: int | None,
        description: str,
        total_amount_cents: int,
        issue_date: datetime | None,
        due_date: datetime | None,
        source_type: str = "",
        source_id: int | None,
        company_id: int | None,
    ) -> None:
        self.customer_id = customer_id
        self.category_id = category_id
        self.description = description
        self.total_amount_cents = total_amount_cents
        self.issue_date = issue_date
        self.due_date = due_date
        self.source_type = source_type
        self.source_id = source_id
        self.company_id = company_id


@dataclass(slots=True, frozen=True)
class CreateReceivableOutput:
    receivable_id: int


class CreateReceivable:
    def __init__(
        self,
        receivable_repo: ReceivableRepository,
    ) -> None:
        self._receivable_repo = receivable_repo

    def execute(self, input_data: CreateReceivableInput) -> CreateReceivableOutput:
        receivable = Receivable(
            customer_id=input_data.customer_id,
            category_id=input_data.category_id,
            description=input_data.description,
            total_amount_cents=input_data.total_amount_cents,
            status=ReceivableStatus.PENDING,
            issue_date=input_data.issue_date or datetime.now(UTC),
            due_date=input_data.due_date,
            source_type=input_data.source_type,
            source_id=input_data.source_id,
        )

        self._receivable_repo.add(receivable)
        return CreateReceivableOutput(receivable_id=receivable.id or 0)


class ReceiveReceivableInput:
    def __init__(
        self,
        *,
        receivable_id: int,
        amount_cents: int,
        received_at: datetime | None = None,
    ) -> None:
        self.receivable_id = receivable_id
        self.amount_cents = amount_cents
        self.received_at = received_at


class ReceiveReceivable:
    def __init__(
        self,
        receivable_repo: ReceivableRepository,
    ) -> None:
        self._receivable_repo = receivable_repo

    def execute(self, input_data: ReceiveReceivableInput) -> None:
        receivable = self._receivable_repo.get_by_id(input_data.receivable_id)
        if receivable is None:
            raise ValueError(f"Receivable {input_data.receivable_id} not found")
        receivable.receive(input_data.amount_cents, input_data.received_at)
        self._receivable_repo.save(receivable)


class CancelReceivableInput:
    def __init__(self, *, receivable_id: int) -> None:
        self.receivable_id = receivable_id


class CancelReceivable:
    def __init__(
        self,
        receivable_repo: ReceivableRepository,
    ) -> None:
        self._receivable_repo = receivable_repo

    def execute(self, input_data: CancelReceivableInput) -> None:
        receivable = self._receivable_repo.get_by_id(input_data.receivable_id)
        if receivable is None:
            raise ValueError(f"Receivable {input_data.receivable_id} not found")
        receivable.cancel()
        self._receivable_repo.save(receivable)


class ListReceivablesInput:
    def __init__(
        self,
        *,
        company_id: int | None = None,
        status: str | None = None,
    ) -> None:
        self.company_id = company_id
        self.status = status


@dataclass(slots=True, frozen=True)
class ReceivableView:
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
class ListReceivablesOutput:
    receivables: tuple


class ListReceivables:
    def __init__(
        self,
        receivable_repo: ReceivableRepository,
    ) -> None:
        self._receivable_repo = receivable_repo

    def execute(self, input_data: ListReceivablesInput) -> list[ReceivableView]:
        receivables = self._receivable_repo.list_by_company(
            company_id=input_data.company_id,
            status=input_data.status,
        )
        return [
            ReceivableView(
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
        ]