"""Integration tests for cash repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.cash.domain.cash_movement import CashMovement, MovementType
from erp.modules.cash.domain.cash_register import CashRegister
from erp.modules.cash.domain.cash_session import CashSession
from erp.modules.cash.infrastructure.models import (
    Base,
    CashMovementModel,
    CashRegisterModel,
    CashSessionModel,
)
from erp.modules.cash.infrastructure.repository import (
    SqlAlchemyCashMovementRepository,
    SqlAlchemyCashRegisterRepository,
    SqlAlchemyCashSessionRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_register_crud(session: Session) -> None:
    repo = SqlAlchemyCashRegisterRepository(session)
    register = CashRegister(name="Caixa 1", terminal_code="T01", company_id=1)
    repo.add(register)

    saved = repo.get_by_id(register.id)
    assert saved is not None
    assert saved.terminal_code == "T01"

    by_terminal = repo.get_by_terminal("T01", company_id=1)
    assert by_terminal is not None
    assert by_terminal.id == register.id


def test_session_crud(session: Session) -> None:
    reg_repo = SqlAlchemyCashRegisterRepository(session)
    sess_repo = SqlAlchemyCashSessionRepository(session)

    register = CashRegister(name="Caixa 1", terminal_code="T01", company_id=1)
    reg_repo.add(register)

    cash_session = CashSession(
        register_id=register.id,
        company_id=1,
        opened_by_user_id=1,
        opened_by_username="admin",
        opening_amount_cents=10000,
    )
    sess_repo.add(cash_session)
    assert cash_session.id is not None

    # Não há sessão aberta ainda (acabou de ser criada mas com status open)
    open_sess = sess_repo.get_open_by_register(register.id)
    assert open_sess is not None
    assert open_sess.id == cash_session.id

    # Fecha a sessão
    cash_session.close(
        closing_amount_cents=10000, closed_by_user_id=1, closed_by_username="admin"
    )
    sess_repo.save(cash_session)

    open_after = sess_repo.get_open_by_register(register.id)
    assert open_after is None


def test_movement_sum(session: Session) -> None:
    reg_repo = SqlAlchemyCashRegisterRepository(session)
    sess_repo = SqlAlchemyCashSessionRepository(session)
    mov_repo = SqlAlchemyCashMovementRepository(session)

    register = CashRegister(name="Caixa 1", terminal_code="T01", company_id=1)
    reg_repo.add(register)

    cash_session = CashSession(register_id=register.id, company_id=1, opening_amount_cents=0)
    sess_repo.add(cash_session)

    mov_repo.add(
        CashMovement(
            session_id=cash_session.id,
            company_id=1,
            movement_type=MovementType.VENDA_DINHEIRO,
            amount_cents=25000,
        )
    )
    mov_repo.add(
        CashMovement(
            session_id=cash_session.id,
            company_id=1,
            movement_type=MovementType.SANGRIA,
            amount_cents=3000,
        )
    )
    mov_repo.add(
        CashMovement(
            session_id=cash_session.id,
            company_id=1,
            movement_type=MovementType.SUPRIMENTO,
            amount_cents=5000,
        )
    )

    assert mov_repo.sum_by_session_and_type(cash_session.id, "venda_dinheiro") == 25000
    assert mov_repo.sum_by_session_and_type(cash_session.id, "sangria") == 3000
    assert mov_repo.sum_by_session_and_type(cash_session.id, "suprimento") == 5000

    movements = mov_repo.list_by_session(cash_session.id)
    assert len(movements) == 3
