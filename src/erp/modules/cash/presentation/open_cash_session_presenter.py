"""Open cash session presenter — orquestra a abertura de sessão sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.engine import Engine

from erp.modules.cash.application.open_cash_session import (
    OpenCashSessionInput,
    OpenCashSessionOutput,
)
from erp.modules.cash.application.services import CashServices
from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound, ValidationError


@runtime_checkable
class OpenCashSessionView(Protocol):
    """Contrato da tela de abertura de sessão de caixa."""

    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def set_registers(self, registers: list[tuple[int, str]]) -> None: ...  # (id, terminal_code)
    def get_selected_register_id(self) -> int | None: ...
    def get_opening_amount_cents(self) -> int: ...
    def accept(self) -> None: ...


class OpenCashSessionPresenter:
    """Valida entrada, abre sessão via caso de uso e atualiza a sessão."""

    def __init__(
        self,
        view: OpenCashSessionView,
        services: CashServices,
        session: CurrentSession,
        engine: Engine,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self._engine = engine

    def load_registers(self) -> None:
        """Carrega caixas disponíveis para a empresa atual."""
        try:
            with SqlAlchemyCashUnitOfWork(self._engine) as uow:
                assert uow.registers is not None
                registers = uow.registers.list_all(company_id=self._session.company_id)
                items = [(r.id, r.terminal_code) for r in registers if r.id is not None]
                self._view.set_registers(items)
        except Exception as exc:
            self._view.show_error(str(exc))

    def open_session(self) -> bool:
        """Tenta abrir a sessão de caixa."""
        register_id = self._view.get_selected_register_id()
        opening_amount_cents = self._view.get_opening_amount_cents()

        if register_id is None:
            self._view.show_error("Selecione um caixa.")
            return False

        if opening_amount_cents < 0:
            self._view.show_error("Valor de abertura não pode ser negativo.")
            return False

        try:
            input_data = OpenCashSessionInput(
                register_id=register_id,
                opening_amount_cents=opening_amount_cents,
                user_id=self._session.user_id,
                username=self._session.username or "",
                company_id=self._session.company_id,
            )
            output: OpenCashSessionOutput = self._services.open_session(input_data)
        except (NotFound, ValidationError) as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

        self._view.show_success(
            f"Sessão aberta no caixa {output.session.register_id} "
            f"(ID: {output.session.id})."
        )
        self._view.accept()
        return True