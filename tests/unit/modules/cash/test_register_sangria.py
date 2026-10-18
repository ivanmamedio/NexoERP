"""Unit tests for RegisterSangria use case (permission + validation)."""

from __future__ import annotations

import pytest

from erp.modules.cash.application.register_sangria import (
    RegisterSangria,
    RegisterSangriaInput,
)
from erp.modules.cash.domain.cash_movement import CashMovement
from erp.modules.cash.domain.cash_session import CashSession
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError


class FakeSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[int, CashSession] = {}

    def add(self, session: CashSession) -> None:
        self._sessions[session.id] = session

    def save(self, session: CashSession) -> None:
        self._sessions[session.id] = session

    def get_by_id(self, session_id: int) -> CashSession | None:
        return self._sessions.get(session_id)

    def get_open_by_register(self, register_id: int) -> CashSession | None:
        return None

    def list_by_company(self, company_id: int | None = None) -> list[CashSession]:
        return list(self._sessions.values())


class FakeMovementRepository:
    def __init__(self) -> None:
        self._movements: list[CashMovement] = []

    def add(self, movement: CashMovement) -> None:
        self._movements.append(movement)

    def list_by_session(self, session_id: int) -> list[CashMovement]:
        return [m for m in self._movements if m.session_id == session_id]

    def sum_by_session_and_type(self, session_id: int, movement_type: str) -> int:
        return sum(
            m.amount_cents
            for m in self._movements
            if m.session_id == session_id and m.movement_type == movement_type
        )


def test_sangria_requires_permission() -> None:
    sess_repo = FakeSessionRepository()
    mov_repo = FakeMovementRepository()
    sess_repo.add(CashSession(id=1, register_id=1, company_id=1, status="open"))

    uc = RegisterSangria(sess_repo, mov_repo, user_permissions={"cash.open_close"})
    with pytest.raises(PermissionDenied, match="cash.sangria"):
        uc.execute(
            RegisterSangriaInput(session_id=1, amount_cents=5000, user_id=1, username="caixa")
        )


def test_sangria_success() -> None:
    sess_repo = FakeSessionRepository()
    mov_repo = FakeMovementRepository()
    sess_repo.add(CashSession(id=1, register_id=1, company_id=1, status="open"))

    uc = RegisterSangria(sess_repo, mov_repo, user_permissions={"cash.sangria"})
    output = uc.execute(
        RegisterSangriaInput(
            session_id=1, amount_cents=5000, description="troco", user_id=1, username="gerente"
        )
    )

    assert output.movement.amount_cents == 5000
    assert output.movement.movement_type == "sangria"
    assert mov_repo.sum_by_session_and_type(1, "sangria") == 5000


def test_sangria_session_closed() -> None:
    sess_repo = FakeSessionRepository()
    mov_repo = FakeMovementRepository()
    sess_repo.add(CashSession(id=1, register_id=1, company_id=1, status="closed"))

    uc = RegisterSangria(sess_repo, mov_repo, user_permissions={"cash.sangria"})
    with pytest.raises(ValidationError, match="fechada"):
        uc.execute(
            RegisterSangriaInput(session_id=1, amount_cents=5000, user_id=1, username="gerente")
        )


def test_sangria_negative_amount() -> None:
    sess_repo = FakeSessionRepository()
    mov_repo = FakeMovementRepository()
    sess_repo.add(CashSession(id=1, register_id=1, company_id=1, status="open"))

    uc = RegisterSangria(sess_repo, mov_repo, user_permissions={"cash.sangria"})
    with pytest.raises(ValidationError, match="positivo"):
        uc.execute(
            RegisterSangriaInput(session_id=1, amount_cents=-5000, user_id=1, username="gerente")
        )
