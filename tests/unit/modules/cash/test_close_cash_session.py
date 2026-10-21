"""Unit tests for CloseCashSession use case — all reconciliation scenarios."""

from __future__ import annotations

import pytest

from erp.modules.cash.application.close_cash_session import (
    CloseCashSession,
    CloseCashSessionInput,
)
from erp.modules.cash.domain.cash_movement import CashMovement, MovementType
from erp.modules.cash.domain.cash_session import CashSession
from erp.shared.domain.errors import NotFound, ValidationError


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


def _setup_session_with_movements() -> tuple[FakeSessionRepository, FakeMovementRepository]:
    sess_repo = FakeSessionRepository()
    mov_repo = FakeMovementRepository()

    # Sessão com abertura R$ 100,00
    sess_repo.add(
        CashSession(id=1, register_id=1, company_id=1, status="open", opening_amount_cents=10000)
    )

    # Vendas em dinheiro R$ 250,00
    mov_repo.add(
        CashMovement(session_id=1, movement_type=MovementType.VENDA_DINHEIRO, amount_cents=25000)
    )
    # Suprimento R$ 50,00
    mov_repo.add(
        CashMovement(session_id=1, movement_type=MovementType.SUPRIMENTO, amount_cents=5000)
    )
    # Sangria R$ 30,00
    mov_repo.add(CashMovement(session_id=1, movement_type=MovementType.SANGRIA, amount_cents=3000))

    return sess_repo, mov_repo


def test_close_session_exact_match() -> None:
    """Fecha com valor exato: sem diferença."""
    sess_repo, mov_repo = _setup_session_with_movements()

    uc = CloseCashSession(sess_repo, mov_repo)
    output = uc.execute(
        CloseCashSessionInput(
            session_id=1,
            closing_amount_cents=37000,
            user_id=1,
            username="gerente",
            total_pix_cents=8000,
            total_card_cents=12000,
        )
    )

    assert output.expected_cash_cents == 37000
    assert output.difference_cents == 0
    assert output.session.is_closed()
    assert output.session.total_sales_cents == 25000
    assert output.session.total_suprimentos_cents == 5000
    assert output.session.total_sangrias_cents == 3000
    assert output.session.total_pix_cents == 8000
    assert output.session.total_card_cents == 12000


def test_close_session_shortage() -> None:
    """Falta de R$ 5,00 (contado 365 em vez de 370)."""
    sess_repo, mov_repo = _setup_session_with_movements()

    uc = CloseCashSession(sess_repo, mov_repo)
    output = uc.execute(
        CloseCashSessionInput(
            session_id=1,
            closing_amount_cents=36500,
            user_id=1,
            username="gerente",
        )
    )

    assert output.expected_cash_cents == 37000
    assert output.difference_cents == -500  # falta


def test_close_session_surplus() -> None:
    """Sobra de R$ 2,00 (contado 372 em vez de 370)."""
    sess_repo, mov_repo = _setup_session_with_movements()

    uc = CloseCashSession(sess_repo, mov_repo)
    output = uc.execute(
        CloseCashSessionInput(
            session_id=1,
            closing_amount_cents=37200,
            user_id=1,
            username="gerente",
        )
    )

    assert output.expected_cash_cents == 37000
    assert output.difference_cents == 200  # sobra


def test_close_session_blind_close() -> None:
    """Fechamento cego: não confere valores, apenas registra."""
    sess_repo, mov_repo = _setup_session_with_movements()

    uc = CloseCashSession(sess_repo, mov_repo)
    output = uc.execute(
        CloseCashSessionInput(
            session_id=1,
            closing_amount_cents=0,
            user_id=1,
            username="gerente",
            blind_close=True,
        )
    )

    assert output.session.blind_close is True
    assert output.session.is_closed()


def test_close_session_already_closed() -> None:
    sess_repo, mov_repo = _setup_session_with_movements()
    # Fecha uma vez
    CloseCashSession(sess_repo, mov_repo).execute(
        CloseCashSessionInput(session_id=1, closing_amount_cents=37000, user_id=1, username="admin")
    )

    # Tenta fechar de novo
    uc = CloseCashSession(sess_repo, mov_repo)
    with pytest.raises(ValidationError, match="fechada"):
        uc.execute(
            CloseCashSessionInput(
                session_id=1, closing_amount_cents=37000, user_id=1, username="admin"
            )
        )


def test_close_session_not_found() -> None:
    sess_repo = FakeSessionRepository()
    mov_repo = FakeMovementRepository()
    uc = CloseCashSession(sess_repo, mov_repo)
    with pytest.raises(NotFound):
        uc.execute(
            CloseCashSessionInput(
                session_id=999, closing_amount_cents=0, user_id=1, username="admin"
            )
        )
