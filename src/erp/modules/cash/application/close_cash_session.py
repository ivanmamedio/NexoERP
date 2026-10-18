"""Close cash session use case — computes totals, difference, and audits."""

from __future__ import annotations

from erp.modules.cash.application.ports import (
    CashMovementRepository,
    CashSessionRepository,
)
from erp.modules.cash.domain.cash_movement import MovementType
from erp.modules.cash.domain.cash_session import CashSession
from erp.shared.domain.errors import NotFound, ValidationError


class CloseCashSessionInput:
    def __init__(
        self,
        *,
        session_id: int,
        closing_amount_cents: int,
        user_id: int | None,
        username: str,
        blind_close: bool = False,
        total_pix_cents: int = 0,
        total_card_cents: int = 0,
        company_id: int | None = None,
    ) -> None:
        self.session_id = session_id
        self.closing_amount_cents = closing_amount_cents
        self.user_id = user_id
        self.username = username
        self.blind_close = blind_close
        self.total_pix_cents = total_pix_cents
        self.total_card_cents = total_card_cents
        self.company_id = company_id


class CloseCashSessionOutput:
    def __init__(
        self,
        session: CashSession,
        difference_cents: int,
        expected_cash_cents: int,
    ) -> None:
        self.session = session
        self.difference_cents = difference_cents
        self.expected_cash_cents = expected_cash_cents


class CloseCashSession:
    """Fecha a sessão de caixa, calcula esperado e diferença."""

    def __init__(
        self,
        session_repo: CashSessionRepository,
        movement_repo: CashMovementRepository,
    ) -> None:
        self._session_repo = session_repo
        self._movement_repo = movement_repo

    def execute(self, input: CloseCashSessionInput) -> CloseCashSessionOutput:
        session = self._session_repo.get_by_id(input.session_id)
        if session is None:
            raise NotFound(f"Sessão de caixa {input.session_id} não encontrada.")
        if not session.is_open():
            raise ValidationError("Sessão de caixa já está fechada.")

        if input.closing_amount_cents < 0:
            raise ValidationError("Valor contado não pode ser negativo.")

        # Calcula totais a partir dos movimentos
        total_sales = self._movement_repo.sum_by_session_and_type(
            input.session_id, MovementType.VENDA_DINHEIRO
        )
        total_suprimentos = self._movement_repo.sum_by_session_and_type(
            input.session_id, MovementType.SUPRIMENTO
        )
        total_sangrias = self._movement_repo.sum_by_session_and_type(
            input.session_id, MovementType.SANGRIA
        )

        session.total_sales_cents = total_sales
        session.total_suprimentos_cents = total_suprimentos
        session.total_sangrias_cents = total_sangrias
        session.total_pix_cents = input.total_pix_cents
        session.total_card_cents = input.total_card_cents

        session.close(
            closing_amount_cents=input.closing_amount_cents,
            closed_by_user_id=input.user_id,
            closed_by_username=input.username,
            blind_close=input.blind_close,
        )
        self._session_repo.save(session)

        return CloseCashSessionOutput(
            session=session,
            difference_cents=session.difference_cents,
            expected_cash_cents=session.expected_cash_cents,
        )
