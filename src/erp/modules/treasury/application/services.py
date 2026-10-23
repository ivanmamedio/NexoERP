"""Application services facade for Treasury."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.engine import Engine

from erp.modules.treasury.application.get_cash_flow import (
    CashFlowInput,
    CashFlowOutput,
    GetCashFlow,
)
from erp.modules.treasury.application.get_category_summary import (
    GetCategorySummary,
    GetCategorySummaryInput,
    GetCategorySummaryOutput,
)
from erp.modules.treasury.application.get_payables_due_soon import (
    GetPayablesDueSoon,
    GetPayablesDueSoonInput,
    GetPayablesDueSoonOutput,
)
from erp.modules.treasury.application.get_receivables_due_soon import (
    GetReceivablesDueSoon,
    GetReceivablesDueSoonInput,
    GetReceivablesDueSoonOutput,
)
from erp.modules.treasury.application.list_payables_by_due_date import (
    ListPayablesByDueDate,
    ListPayablesByDueDateInput,
    ListPayablesByDueDateOutput,
)
from erp.modules.treasury.application.list_receivables_by_due_date import (
    ListReceivablesByDueDate,
    ListReceivablesByDueDateInput,
    ListReceivablesByDueDateOutput,
)
from erp.modules.treasury.infrastructure.unit_of_work import (
    SqlAlchemyTreasuryUnitOfWork,
)


class TreasuryServices:
    """Facade de casos de uso de tesouraria sobre SQLAlchemy."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_cash_flow(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
    ) -> CashFlowOutput:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            result = GetCashFlow(uow.financial_entries).execute(
                CashFlowInput(
                    start_date=start_date,
                    end_date=end_date,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def list_payables_by_due_date(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
        status: str | None = None,
    ) -> ListPayablesByDueDateOutput:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.payables is not None
            result = ListPayablesByDueDate(uow.payables).execute(
                ListPayablesByDueDateInput(
                    start_date=start_date,
                    end_date=end_date,
                    company_id=company_id,
                    status=status,
                )
            )
            uow.commit()
            return result

    def list_receivables_by_due_date(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
        status: str | None = None,
    ) -> ListReceivablesByDueDateOutput:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.receivables is not None
            result = ListReceivablesByDueDate(uow.receivables).execute(
                ListReceivablesByDueDateInput(
                    start_date=start_date,
                    end_date=end_date,
                    company_id=company_id,
                    status=status,
                )
            )
            uow.commit()
            return result

    def get_payables_due_soon(
        self,
        *,
        days_ahead: int = 7,
        company_id: int | None = None,
    ) -> GetPayablesDueSoonOutput:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.payables is not None
            result = GetPayablesDueSoon(uow.payables).execute(
                GetPayablesDueSoonInput(
                    days_ahead=days_ahead,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def get_receivables_due_soon(
        self,
        *,
        days_ahead: int = 7,
        company_id: int | None = None,
    ) -> GetReceivablesDueSoonOutput:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.receivables is not None
            result = GetReceivablesDueSoon(uow.receivables).execute(
                GetReceivablesDueSoonInput(
                    days_ahead=days_ahead,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def get_category_summary(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
    ) -> GetCategorySummaryOutput:
        with SqlAlchemyTreasuryUnitOfWork(self._engine) as uow:
            assert uow.financial_entries is not None
            assert uow.financial_categories is not None
            result = GetCategorySummary(
                uow.financial_entries,
                uow.financial_categories,
            ).execute(
                GetCategorySummaryInput(
                    start_date=start_date,
                    end_date=end_date,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result
