"""Create payable use case with installments and recurrence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from erp.modules.treasury.application.ports import PayableRepository
from erp.modules.treasury.domain.payable import (
    Payable,
    PayableStatus,
)


class PayableInstallmentInput:
    def __init__(
        self,
        *,
        installment_number: int,
        due_date: datetime,
        amount_cents: int,
    ) -> None:
        self.installment_number = installment_number
        self.due_date = due_date
        self.amount_cents = amount_cents


@dataclass(slots=True, frozen=True)
class CreatePayableInput:
    supplier_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    issue_date: datetime | None
    recurrence_type: str = "none"
    recurrence_count: int = 1
    first_due_date: datetime | None = None
    interval_days: int = 30
    source_type: str = ""
    source_id: int | None = None
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class CreatePayableOutput:
    payable_id: int


class CreatePayable:
    def __init__(
        self,
        payable_repo: PayableRepository,
    ) -> None:
        self._payable_repo = payable_repo

    def execute(self, input_data: CreatePayableInput) -> CreatePayableOutput:
        payable = Payable(
            company_id=input_data.company_id,
            supplier_id=input_data.supplier_id,
            category_id=input_data.category_id,
            description=input_data.description,
            total_amount_cents=input_data.total_amount_cents,
            status=PayableStatus.PENDING,
            issue_date=input_data.issue_date or datetime.now(UTC),
            recurrence_type=input_data.recurrence_type,
            recurrence_count=input_data.recurrence_count,
            source_type=input_data.source_type,
            source_id=input_data.source_id,
        )

        if input_data.recurrence_type != "none" and input_data.recurrence_count > 1:
            first_due = input_data.first_due_date or datetime.now(UTC)
            payable.create_installments(
                first_due_date=first_due,
                interval_days=input_data.interval_days,
            )
        elif input_data.first_due_date:
            # Single installment with custom due date
            payable.add_installment(
                installment_number=1,
                due_date=input_data.first_due_date,
                amount_cents=input_data.total_amount_cents,
            )

        self._payable_repo.add(payable)
        return CreatePayableOutput(payable_id=payable.id or 0)


class PayPayableInput:
    def __init__(
        self,
        *,
        payable_id: int,
        installment_number: int,
        amount_cents: int,
        paid_at: datetime | None = None,
    ) -> None:
        self.payable_id = payable_id
        self.installment_number = installment_number
        self.amount_cents = amount_cents
        self.paid_at = paid_at


class PayPayable:
    def __init__(
        self,
        payable_repo: PayableRepository,
    ) -> None:
        self._payable_repo = payable_repo

    def execute(self, input_data: PayPayableInput) -> None:
        payable = self._payable_repo.get_by_id(input_data.payable_id)
        if payable is None:
            raise ValueError(f"Payable {input_data.payable_id} not found")
        payable.pay_installment(
            installment_number=input_data.installment_number,
            amount_cents=input_data.amount_cents,
            paid_at=input_data.paid_at,
        )
        self._payable_repo.save(payable)


class CancelPayableInput:
    def __init__(self, *, payable_id: int) -> None:
        self.payable_id = payable_id


class CancelPayable:
    def __init__(
        self,
        payable_repo: PayableRepository,
    ) -> None:
        self._payable_repo = payable_repo

    def execute(self, input_data: CancelPayableInput) -> None:
        payable = self._payable_repo.get_by_id(input_data.payable_id)
        if payable is None:
            raise ValueError(f"Payable {input_data.payable_id} not found")
        payable.cancel()
        self._payable_repo.save(payable)


class ListPayablesInput:
    def __init__(
        self,
        *,
        company_id: int | None = None,
        status: str | None = None,
    ) -> None:
        self.company_id = company_id
        self.status = status


@dataclass(slots=True, frozen=True)
class PayableView:
    payable_id: int
    supplier_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    recurrence_type: str
    recurrence_count: int
    total_paid_cents: int
    total_pending_cents: int


@dataclass(slots=True, frozen=True)
class ListPayablesOutput:
    payables: tuple[PayableView, ...]


class ListPayables:
    def __init__(
        self,
        payable_repo: PayableRepository,
    ) -> None:
        self._payable_repo = payable_repo

    def execute(self, input_data: ListPayablesInput) -> ListPayablesOutput:
        payables = self._payable_repo.list_by_company(
            company_id=input_data.company_id,
            status=input_data.status,
        )
        views = tuple(
            PayableView(
                payable_id=p.id or 0,
                supplier_id=p.supplier_id,
                category_id=p.category_id,
                description=p.description,
                total_amount_cents=p.total_amount_cents,
                status=p.status,
                issue_date=p.issue_date,
                recurrence_type=p.recurrence_type,
                recurrence_count=p.recurrence_count,
                total_paid_cents=p.paid_amount_cents,
                total_pending_cents=p.pending_amount_cents,
            )
            for p in payables
        )
        return ListPayablesOutput(payables=views)