"""Close cash session presenter — orquestra o fechamento de sessão sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.engine import Engine

from erp.modules.cash.application.close_cash_session import (
    CloseCashSessionInput,
)
from erp.modules.cash.application.services import CashServices
from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound, ValidationError


@runtime_checkable
class CloseCashSessionView(Protocol):
    """Contrato da tela de fechamento de sessão de caixa."""

    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def set_session_info(self, session_id: int, expected_cash: int) -> None: ...
    def get_counted_amount_cents(self) -> int: ...
    def is_blind_close(self) -> bool: ...
    def get_pix_cents(self) -> int: ...
    def get_card_cents(self) -> int: ...
    def accept(self) -> None: ...


class CloseCashSessionPresenter:
    """Valida entrada, fecha sessão via caso de uso."""

    def __init__(
        self,
        view: CloseCashSessionView,
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

    def load_session(self) -> None:
        """Carrega info da sessão e calcula esperado para exibir."""
        try:
            with SqlAlchemyCashUnitOfWork(self._engine) as uow:
                assert uow.sessions is not None and uow.movements is not None

                cash_session = uow.sessions.get_by_id(self._session_id)
                if cash_session is None:
                    self._view.show_error("Sessão não encontrada.")
                    return
                if not cash_session.is_open():
                    self._view.show_error("Sessão já está fechada.")
                    return

                # Calcula esperado para exibir
                total_sales = uow.movements.sum_by_session_and_type(
                    self._session_id, "venda_dinheiro"
                )
                total_suprimentos = uow.movements.sum_by_session_and_type(
                    self._session_id, "suprimento"
                )
                total_sangrias = uow.movements.sum_by_session_and_type(self._session_id, "sangria")

                expected = (
                    cash_session.opening_amount_cents
                    + total_sales
                    + total_suprimentos
                    - total_sangrias
                )

                self._view.set_session_info(cash_session.id or 0, expected)
        except Exception as exc:
            self._view.show_error(str(exc))

    def close_session(self) -> bool:
        """Executa fechamento da sessão."""
        counted_amount_cents = self._view.get_counted_amount_cents()
        blind_close = self._view.is_blind_close()
        pix_cents = self._view.get_pix_cents()
        card_cents = self._view.get_card_cents()

        if counted_amount_cents < 0:
            self._view.show_error("Valor contado não pode ser negativo.")
            return False

        try:
            input_data = CloseCashSessionInput(
                session_id=self._session_id,
                closing_amount_cents=counted_amount_cents,
                user_id=self._session.user_id,
                username=self._session.username or "",
                blind_close=blind_close,
                total_pix_cents=pix_cents,
                total_card_cents=card_cents,
                company_id=self._session.company_id,
            )
            output = self._services.close_session(input_data)
        except (NotFound, ValidationError) as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

        diff_msg = (
            f"Sobrou: R$ {abs(output.difference_cents) / 100:.2f}"
            if output.difference_cents > 0
            else f"Faltou: R$ {abs(output.difference_cents) / 100:.2f}"
            if output.difference_cents < 0
            else "Fechamento exato (diferença zero)"
        )

        blind_msg = " (Fechamento cego)" if output.session.blind_close else ""

        self._view.show_success(
            f"Sessão fechada.{blind_msg}\n"
            f"Esperado: R$ {output.expected_cash_cents / 100:.2f}\n"
            f"Contado: R$ {output.session.closing_amount_cents / 100:.2f}\n"
            f"{diff_msg}"
        )
        return True
