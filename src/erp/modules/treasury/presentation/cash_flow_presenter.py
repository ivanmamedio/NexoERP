"""Cash flow presenter — orquestra a tela de fluxo de caixa."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from erp.modules.treasury.application.get_cash_flow import (
    CashFlowOutput,
)
from erp.modules.treasury.application.services import TreasuryServices
from erp.shared.application.session import CurrentSession


@runtime_checkable
class CashFlowView(Protocol):
    """Contrato da tela de fluxo de caixa."""

    def show_error(self, message: str) -> None: ...
    def set_results(self, output: CashFlowOutput) -> None: ...
    def set_date_range(self, start_date: datetime, end_date: datetime) -> None: ...
    def get_start_date(self) -> datetime: ...
    def get_end_date(self) -> datetime: ...
    def accept(self) -> None: ...


class CashFlowPresenter:
    """Calcula e exibe o fluxo de caixa por período."""

    def __init__(
        self,
        view: CashFlowView,
        services: TreasuryServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def load_cash_flow(self) -> None:
        """Calcula o fluxo de caixa para o período selecionado."""
        company_id = self._session.company_id
        if company_id is None:
            self._view.show_error("Nenhuma empresa ativa na sessão.")
            return

        try:
            output = self._services.get_cash_flow(
                start_date=self._view.get_start_date(),
                end_date=self._view.get_end_date(),
                company_id=company_id,
            )
            self._view.set_results(output)
        except Exception as exc:  # pragma: no cover
            self._view.show_error(f"Erro ao calcular fluxo de caixa: {exc}")
