"""Get closing report use case — structured report for the shift."""

from __future__ import annotations

from erp.modules.cash.application.ports import CashSessionRepository
from erp.modules.cash.domain.closing_report import CashClosingReport
from erp.shared.domain.errors import NotFound


class GetClosingReportInput:
    def __init__(self, *, session_id: int) -> None:
        self.session_id = session_id


class GetClosingReport:
    def __init__(self, session_repo: CashSessionRepository) -> None:
        self._session_repo = session_repo

    def execute(self, input: GetClosingReportInput) -> CashClosingReport:
        session = self._session_repo.get_by_id(input.session_id)
        if session is None:
            raise NotFound(f"Sessão de caixa {input.session_id} não encontrada.")

        return CashClosingReport(
            session_id=session.id or 0,
            company_id=session.company_id,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            opened_by_username=session.opened_by_username,
            closed_by_username=session.closed_by_username,
            opening_amount_cents=session.opening_amount_cents,
            total_sales_cents=session.total_sales_cents,
            total_suprimentos_cents=session.total_suprimentos_cents,
            total_sangrias_cents=session.total_sangrias_cents,
            total_pix_cents=session.total_pix_cents,
            total_card_cents=session.total_card_cents,
            expected_cash_cents=session.expected_cash_cents,
            counted_cash_cents=session.closing_amount_cents,
            difference_cents=session.difference_cents,
            blind_close=session.blind_close,
            status=session.status,
        )
