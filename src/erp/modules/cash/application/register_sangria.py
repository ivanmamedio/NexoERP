"""Register sangria use case — requires cash.sangria permission."""

from __future__ import annotations

from erp.modules.cash.application.ports import CashMovementRepository, CashSessionRepository
from erp.modules.cash.domain.cash_movement import CashMovement, MovementType
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError


class RegisterSangriaInput:
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


class RegisterSangriaOutput:
    def __init__(self, movement: CashMovement) -> None:
        self.movement = movement


class RegisterSangria:
    """Registra uma sangria (retirada de dinheiro do caixa)."""

    def __init__(
        self,
        session_repo: CashSessionRepository,
        movement_repo: CashMovementRepository,
        user_permissions: set[str],
    ) -> None:
        self._session_repo = session_repo
        self._movement_repo = movement_repo
        self._user_permissions = user_permissions

    def execute(self, input: RegisterSangriaInput) -> RegisterSangriaOutput:
        if "cash.sangria" not in self._user_permissions:
            raise PermissionDenied("Usuário não tem permissão para sangria (cash.sangria).")

        session = self._session_repo.get_by_id(input.session_id)
        if session is None:
            raise NotFound(f"Sessão de caixa {input.session_id} não encontrada.")
        if not session.is_open():
            raise ValidationError("Sessão de caixa está fechada.")

        if input.amount_cents <= 0:
            raise ValidationError("Valor da sangria deve ser positivo.")

        movement = CashMovement(
            session_id=input.session_id,
            company_id=input.company_id or session.company_id,
            movement_type=MovementType.SANGRIA,
            amount_cents=input.amount_cents,
            description=input.description,
            user_id=input.user_id,
            username=input.username,
        )
        self._movement_repo.add(movement)
        return RegisterSangriaOutput(movement=movement)
