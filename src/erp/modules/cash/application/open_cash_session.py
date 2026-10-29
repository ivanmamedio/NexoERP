"""Open cash session use case."""

from __future__ import annotations

from erp.modules.cash.application.ports import CashRegisterRepository, CashSessionRepository
from erp.modules.cash.domain.cash_session import CashSession
from erp.shared.domain.errors import NotFound, ValidationError


class OpenCashSessionInput:
    def __init__(
        self,
        *,
        register_id: int,
        opening_amount_cents: int,
        user_id: int | None,
        username: str,
        company_id: int | None = None,
    ) -> None:
        self.register_id = register_id
        self.opening_amount_cents = opening_amount_cents
        self.user_id = user_id
        self.username = username
        self.company_id = company_id


class OpenCashSessionOutput:
    def __init__(self, session: CashSession) -> None:
        self.session = session


class OpenCashSession:
    """Abre uma sessão de caixa. Regra: uma sessão aberta por terminal."""

    def __init__(
        self,
        session_repo: CashSessionRepository,
        register_repo: CashRegisterRepository,
    ) -> None:
        self._session_repo = session_repo
        self._register_repo = register_repo

    def execute(self, input: OpenCashSessionInput) -> OpenCashSessionOutput:
        register = self._register_repo.get_by_id(input.register_id)
        if register is None:
            raise NotFound(f"Caixa {input.register_id} não encontrado.")

        existing = self._session_repo.get_open_by_register(input.register_id)
        if existing is not None:
            raise ValidationError(f"Já existe uma sessão aberta no caixa {register.terminal_code}.")

        if input.opening_amount_cents < 0:
            raise ValidationError("Valor de abertura não pode ser negativo.")

        session = CashSession(
            register_id=input.register_id,
            company_id=input.company_id or register.company_id,
            opened_by_user_id=input.user_id,
            opened_by_username=input.username,
            opening_amount_cents=input.opening_amount_cents,
            status="open",
        )
        self._session_repo.add(session)
        return OpenCashSessionOutput(session=session)
