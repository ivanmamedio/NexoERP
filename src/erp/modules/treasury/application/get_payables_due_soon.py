"""Get payables due soon use case (alertas de vencimento)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from erp.modules.treasury.application.list_payables_by_due_date import (
    ListPayablesByDueDate,
    ListPayablesByDueDateInput,
)
from erp.modules.treasury.application.ports import PayableRepository


@runtime_checkable
class PayableDueSoonView(Protocol):
    payable_id: int
    supplier_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    installments: tuple[PayableInstallmentView, ...]


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
class PayableDueSoonViewImpl:
    payable_id: int
    supplier_id: int | None
    category_id: int | None
    description: str
    total_amount_cents: int
    status: str
    issue_date: datetime | None
    installments: tuple[PayableInstallmentViewImpl, ...]
    # Parcela mais próxima do vencimento
    next_due_date: datetime | None
    next_due_amount_cents: int


@dataclass(slots=True, frozen=True)
class GetPayablesDueSoonInput:
    days_ahead: int = 7
    company_id: int | None = None


@dataclass(slots=True, frozen=True)
class GetPayablesDueSoonOutput:
    payables: tuple[PayableDueSoonViewImpl, ...]
    total_due_cents: int
    overdue_count: int
    due_soon_count: int


class GetPayablesDueSoon:
    """Busca contas a pagar vencidas ou prestes a vencer (alertas)."""

    def __init__(self, repo: PayableRepository) -> None:
        self._list_by_due = ListPayablesByDueDate(repo)

    def execute(self, input_data: GetPayablesDueSoonInput) -> GetPayablesDueSoonOutput:
        now = datetime.now(UTC)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        # Adiciona dias à frente
        from datetime import timedelta

        end_date = end_date + timedelta(days=input_data.days_ahead)

        result = self._list_by_due.execute(
            ListPayablesByDueDateInput(
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

        for p in result.payables:
            # Filtrar apenas parcelas pendentes
            pending_installments = [i for i in p.installments if i.status == "pending"]
            if not pending_installments:
                continue

            # Ordenar por data de vencimento
            pending_installments.sort(key=lambda x: x.due_date)

            next_due = pending_installments[0]
            next_due_date = next_due.due_date
            next_due_amount = next_due.amount_cents

            if next_due_date <= now:
                overdue_count += 1
            else:
                due_soon_count += 1

            total_due += sum(i.amount_cents for i in pending_installments)

            due_soon.append(
                PayableDueSoonViewImpl(
                    payable_id=p.payable_id,
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
                    next_due_date=next_due_date,
                    next_due_amount_cents=next_due_amount,
                )
            )

        return GetPayablesDueSoonOutput(
            payables=tuple(due_soon),
            total_due_cents=total_due,
            overdue_count=overdue_count,
            due_soon_count=due_soon_count,
        )
