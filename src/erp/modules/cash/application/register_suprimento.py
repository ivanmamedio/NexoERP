"""Register suprimento use case (entrada de dinheiro no caixa)."""

from __future__ import annotations

from erp.modules.cash.application.ports import CashMovementRepository, CashSessionRepository
from erp.modules.cash.domain.cash_movement import CashMovement, MovementType
from erp.shared.domain.errors import NotFound, ValidationError


class RegisterSuprimentoInput:
    def __init__(
        self,
        *,
        session_id: int,
        amount_cents: int,
        description: str = "",
        user_id: int | None = None,
        username: str = "",
        company_id: int | None = None,
    ) -> None:
        self.session_id = session_id
        self.amount_cents = amount_cents
        self.description = description
        self.user_id = user_id
        self.username = username
        self.company_id = company_id


class RegisterSuprimentoOutput:
    def __init__(self, movement: CashMovement) -> None:
        self.movement = movement


class RegisterSuprimento:
    """Registra um suprimento (entrada de dinheiro no caixa)."""

    def __init__(
        self,
        session_repo: CashSessionRepository,
        movement_repo: CashMovementRepository,
    ) -> None:
        self._session_repo = session_repo
        self._movement_repo = movement_repo

    def execute(self, input: RegisterSuprimentoInput) -> RegisterSuprimentoOutput:
        session = self._session_repo.get_by_id(input.session_id)
        if session is None:
            raise NotFound(f"Sessão de caixa {input.session_id} não encontrada.")
        if not session.is_open():
            raise ValidationError("Sessão de caixa está fechada.")

        if input.amount_cents <= 0:
            raise ValidationError("Valor do suprimento deve ser positivo.")

        movement = CashMovement(
            session_id=input.session_id,
            company_id=input.company_id or session.company_id,
            movement_type=MovementType.SUPRIMENTO,
            amount_cents=input.amount_cents,
            description=input.description,
            user_id=input.user_id,
            username=input.username,
        )
        self._movement_repo.add(movement)
        return RegisterSuprimentoOutput(movement=movement)
