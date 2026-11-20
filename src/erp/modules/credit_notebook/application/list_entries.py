"""List credit entries use case."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.credit_notebook.application.ports import CreditEntryRepository


@dataclass(slots=True, frozen=True)
class ListCreditEntriesInput:
    customer_id: int | None = None
    company_id: int | None = None
    status: str | None = None
    entry_type: str | None = None


@dataclass(slots=True, frozen=True)
class CreditEntryView:
    entry_id: int
    customer_id: int
    customer_name: str
    entry_type: str
    description: str
    amount_cents: int
    status: str
    due_date: str | None
    paid_amount_cents: int
    pending_amount_cents: int
    created_at: str
    created_by_username: str


@dataclass(slots=True, frozen=True)
class ListCreditEntriesOutput:
    entries: tuple[CreditEntryView, ...]


class ListCreditEntries:
    def __init__(self, repository: CreditEntryRepository) -> None:
        self._repository = repository

    def execute(self, input_data: ListCreditEntriesInput) -> ListCreditEntriesOutput:
        if input_data.customer_id is not None:
            entries = self._repository.list_by_customer(input_data.customer_id, input_data.status)
        else:
            entries = self._repository.list_by_company(input_data.company_id, input_data.status)

        # Filter by entry_type if provided
        if input_data.entry_type:
            entries = [e for e in entries if e.entry_type == input_data.entry_type]

        views = tuple(
            CreditEntryView(
                entry_id=e.id or 0,
                customer_id=e.customer_id,
                customer_name="",  # Will be populated by presenter if needed
                entry_type=e.entry_type,
                description=e.description,
                amount_cents=e.amount_cents,
                status=e.status,
                due_date=e.due_date.strftime("%d/%m/%Y") if e.due_date else None,
                paid_amount_cents=e.paid_amount_cents,
                pending_amount_cents=e.pending_amount_cents,
                created_at=e.created_at.strftime("%d/%m/%Y %H:%M"),
                created_by_username=e.created_by_username,
            )
            for e in entries
        )
        return ListCreditEntriesOutput(entries=views)
