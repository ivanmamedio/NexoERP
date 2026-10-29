"""Closing report presenter — orquestra a exibição do relatório
de fechamento sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.engine import Engine

from erp.modules.cash.application.get_closing_report import (
    GetClosingReportInput,
)
from erp.modules.cash.application.services import CashServices
from erp.modules.cash.domain.closing_report import CashClosingReport
from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound


@runtime_checkable
class ClosingReportView(Protocol):
    """Contrato da tela de relatório de fechamento."""

    def show_error(self, message: str) -> None: ...
    def set_report(self, report: CashClosingReport) -> None: ...
    def accept(self) -> None: ...


class ClosingReportPresenter:
    """Carrega relatório de fechamento e passa para a view."""

    def __init__(
        self,
        view: ClosingReportView,
        services: CashServices,
        session: CurrentSession,
        session_id: int,
        engine: Engine,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self._session_id = session_id
        self._engine = engine

    def load_report(self) -> None:
        """Carrega o relatório de fechamento."""
        try:
            with SqlAlchemyCashUnitOfWork(self._engine) as uow:
                assert uow.sessions is not None
                session_obj = uow.sessions.get_by_id(self._session_id)
                if session_obj is None:
                    self._view.show_error("Sessão não encontrada.")
                    return

                input_data = GetClosingReportInput(session_id=self._session_id)
                report = self._services.get_closing_report(input_data)
                self._view.set_report(report)
        except NotFound as exc:
            self._view.show_error(str(exc))
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
