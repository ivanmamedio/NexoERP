"""List payables by due date range use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from erp.modules.treasury.application.ports import PayableRepository


@runtime_checkable
class PayableView(Protocol):
    payable_id: int
    supplier_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    installments: list[PayableInstallmentView]


@runtime_checkable
class PayableInstallmentView(Protocol):
    installment_number: int
    due_date: datetime
    amount_cents: int
    status: str
    paid_at: datetime | None
    paid_amount_cents: int


@dataclass(slots=True, frozen=True)
class PayableInstallmentViewImpl:
    installment_number: int
    due_date: datetime
    amount_cents: int
    status: str
    paid_at: datetime | None
    paid_amount_cents: int


@dataclass(slots=True, frozen=True)
class PayableViewImpl:
    payable_id: int
    supplier_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    installments: tuple[PayableInstallmentViewImpl, ...]


@dataclass(slots=True, frozen=True)
class ListPayablesByDueDateInput:
    start_date: datetime
    end_date: datetime
    company_id: int | None = None
    status: str | None = None


@dataclass(slots=True, frozen=True)
class ListPayablesByDueDateOutput:
    payables: tuple[PayableViewImpl, ...]


class ListPayablesByDueDate:
    """Lista contas a pagar com vencimento no intervalo especificado."""

    def __init__(self, repo: PayableRepository) -> None:
        self._repo = repo

    def execute(self, input_data: ListPayablesByDueDateInput) -> ListPayablesByDueDateOutput:
        payables = self._repo.list_by_due_date_range(
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            company_id=input_data.company_id,
            status=input_data.status,
        )
        views = tuple(
            PayableViewImpl(
                payable_id=p.id or 0,
                supplier_id=p.supplier_id,
                category_id=p.category_id,
                description=p.description,
                total_amount_cents=p.total_amount_cents,
                status=p.status,
                issue_date=p.issue_date,
                installments=tuple(
                    PayableInstallmentViewImpl(
                        installment_number=i.installment_number,
                        due_date=i.due_date,
                        amount_cents=i.amount_cents,
                        status=i.status,
                        paid_at=i.paid_at,
                        paid_amount_cents=i.paid_amount_cents,
                    )
                    for i in p.installments
                ),
            )
            for p in payables
        )
        return ListPayablesByDueDateOutput(payables=views)
