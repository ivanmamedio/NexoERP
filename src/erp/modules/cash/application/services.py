"""Application services facade for Cash."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.cash.application.close_cash_session import (
    CloseCashSession,
    CloseCashSessionInput,
    CloseCashSessionOutput,
)
from erp.modules.cash.application.get_closing_report import (
    GetClosingReport,
    GetClosingReportInput,
)
from erp.modules.cash.application.open_cash_session import (
    OpenCashSession,
    OpenCashSessionInput,
    OpenCashSessionOutput,
)
from erp.modules.cash.application.register_sangria import (
    RegisterSangria,
    RegisterSangriaInput,
    RegisterSangriaOutput,
)
from erp.modules.cash.application.register_suprimento import (
    RegisterSuprimento,
    RegisterSuprimentoInput,
    RegisterSuprimentoOutput,
)
from erp.modules.cash.domain.closing_report import CashClosingReport
from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
from erp.shared.application.events import EventBus


class CashServices:
    """Facade de casos de uso de caixa sobre SQLAlchemy (1 transação por operação)."""

    def __init__(
        self,
        engine: Engine,
        event_bus: EventBus,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._user_permissions = user_permissions or set()

    def open_session(self, input: OpenCashSessionInput) -> OpenCashSessionOutput:
        with SqlAlchemyCashUnitOfWork(self._engine) as uow:
            assert uow.sessions is not None and uow.registers is not None
            result = OpenCashSession(uow.sessions, uow.registers).execute(input)
            uow.commit()
            return result

    def register_sangria(self, input: RegisterSangriaInput) -> RegisterSangriaOutput:
        with SqlAlchemyCashUnitOfWork(self._engine) as uow:
            assert uow.sessions is not None and uow.movements is not None
            result = RegisterSangria(uow.sessions, uow.movements, self._user_permissions).execute(
                input
            )
            uow.commit()
            return result

    def register_suprimento(self, input: RegisterSuprimentoInput) -> RegisterSuprimentoOutput:
        with SqlAlchemyCashUnitOfWork(self._engine) as uow:
            assert uow.sessions is not None and uow.movements is not None
            result = RegisterSuprimento(uow.sessions, uow.movements).execute(input)
            uow.commit()
            return result

    def close_session(self, input: CloseCashSessionInput) -> CloseCashSessionOutput:
        with SqlAlchemyCashUnitOfWork(self._engine) as uow:
            assert uow.sessions is not None and uow.movements is not None
            result = CloseCashSession(uow.sessions, uow.movements, self._event_bus).execute(input)
            uow.commit()
            return result

    def get_closing_report(self, input: GetClosingReportInput) -> CashClosingReport:
        with SqlAlchemyCashUnitOfWork(self._engine) as uow:
            assert uow.sessions is not None
            return GetClosingReport(uow.sessions).execute(input)
