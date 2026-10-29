"""Treasury dashboard presenter — orquestra a tela principal de tesouraria."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.treasury.application.services import TreasuryServices
from erp.modules.treasury.presentation.protocols import TreasuryDashboardView
from erp.shared.application.session import CurrentSession


class TreasuryDashboardPresenter:
    """Carrega dados de todas as abas do dashboard de tesouraria."""

    def __init__(
        self,
        view: TreasuryDashboardView,
        services: TreasuryServices,
        session: CurrentSession,
        engine: Engine,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self._engine = engine

    def load_all(self) -> None:
        """Carrega dados de todas as abas."""
        company_id = self._session.company_id
        if company_id is None:
            self._view.show_error("Nenhuma empresa ativa na sessão.")
            return

        try:
            # 1. Fluxo de caixa
            cf = self._services.get_cash_flow(
                start_date=self._view.get_start_date(),
                end_date=self._view.get_end_date(),
                company_id=company_id,
            )
            self._view.set_cash_flow(cf)

            # 2. Contas a pagar (com filtro de data)
            pay = self._services.list_payables_by_due_date(
                start_date=self._view.get_start_date(),
                end_date=self._view.get_end_date(),
                company_id=company_id,
                status="pending",
            )
            self._view.set_payables(pay)

            # 3. Contas a receber (com filtro de data)
            recv = self._services.list_receivables_by_due_date(
                start_date=self._view.get_start_date(),
                end_date=self._view.get_end_date(),
                company_id=company_id,
                status="pending",
            )
            self._view.set_receivables(recv)

            # 4. Alertas
            pay_alerts = self._services.get_payables_due_soon(
                days_ahead=self._view.get_days_ahead(),
                company_id=company_id,
            )
            recv_alerts = self._services.get_receivables_due_soon(
                days_ahead=self._view.get_days_ahead(),
                company_id=company_id,
            )
            self._view.set_alerts(pay_alerts, recv_alerts)

            # 5. Resumo por categoria
            cat = self._services.get_category_summary(
                start_date=self._view.get_start_date(),
                end_date=self._view.get_end_date(),
                company_id=company_id,
            )
            self._view.set_category_summary(cat)

        except Exception as exc:  # pragma: no cover
            self._view.show_error(f"Erro ao carregar tesouraria: {exc}")
