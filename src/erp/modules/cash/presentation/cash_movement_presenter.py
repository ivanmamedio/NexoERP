"""Cash movement presenter — orquestra sangria e suprimento sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.engine import Engine

from erp.modules.cash.application.register_sangria import (
    RegisterSangriaInput,
    RegisterSangriaOutput,
)
from erp.modules.cash.application.register_suprimento import (
    RegisterSuprimentoInput,
    RegisterSuprimentoOutput,
)
from erp.modules.cash.application.services import CashServices
from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError


class MovementType:
    SANGRIA = "sangria"
    SUPRIMENTO = "suprimento"


@runtime_checkable
class CashMovementView(Protocol):
    """Contrato da tela de movimento de caixa (sangria/suprimento)."""

    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def set_session_info(self, session_id: int, status: str) -> None: ...
    def get_amount_cents(self) -> int: ...
    def get_description(self) -> str: ...
    def accept(self) -> None: ...


class CashMovementPresenter:
    """Valida entrada, executa movimento via caso de uso."""

    def __init__(
        self,
        view: CashMovementView,
        services: CashServices,
        session: CurrentSession,
        movement_type: str,
        session_id: int,
        engine: Engine,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self._movement_type = movement_type
        self._session_id = session_id
        self._engine = engine

    def load_session(self) -> None:
        """Carrega info da sessão para exibir."""
        try:
            with SqlAlchemyCashUnitOfWork(self._engine) as uow:
                assert uow.sessions is not None
                cash_session = uow.sessions.get_by_id(self._session_id)
                if cash_session is None:
                    self._view.show_error("Sessão não encontrada.")
                    return
                status = "Aberta" if cash_session.is_open() else "Fechada"
                self._view.set_session_info(cash_session.id or 0, status)
        except Exception as exc:
            self._view.show_error(str(exc))

    def execute_movement(self) -> bool:
        """Executa sangria ou suprimento."""
        amount_cents = self._view.get_amount_cents()
        description = self._view.get_description()

        if amount_cents <= 0:
            self._view.show_error("Valor deve ser positivo.")
            return False

        try:
            if self._movement_type == MovementType.SANGRIA:
                sangria_input = RegisterSangriaInput(
                    session_id=self._session_id,
                    amount_cents=amount_cents,
                    description=description,
                    user_id=self._session.user_id,
                    username=self._session.username or "",
                    company_id=self._session.company_id,
                )
                output: RegisterSangriaOutput | RegisterSuprimentoOutput = (
                    self._services.register_sangria(sangria_input)
                )
            else:
                suprimento_input = RegisterSuprimentoInput(
                    session_id=self._session_id,
                    amount_cents=amount_cents,
                    description=description,
                    user_id=self._session.user_id,
                    username=self._session.username or "",
                    company_id=self._session.company_id,
                )
                output = self._services.register_suprimento(suprimento_input)
        except (NotFound, PermissionDenied, ValidationError) as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

        self._view.show_success(
            f"{'Sangria' if self._movement_type == MovementType.SANGRIA else 'Suprimento'} "
            f"registrada: R$ {output.movement.amount_cents / 100:.2f}"
        )
        return True
