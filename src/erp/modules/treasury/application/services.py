"""Application services facade for Treasury."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.engine import Engine

from erp.modules.treasury.application.get_cash_flow import (
    CashFlowInput,
    CashFlowOutput,
    GetCashFlow,
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
