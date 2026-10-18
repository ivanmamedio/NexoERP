"""Unit tests for OpenCashSession use case."""

from __future__ import annotations

import pytest

from erp.modules.cash.application.open_cash_session import (
    OpenCashSession,
    OpenCashSessionInput,
)
from erp.modules.cash.domain.cash_register import CashRegister
from erp.modules.cash.domain.cash_session import CashSession
from erp.shared.domain.errors import NotFound, ValidationError


class FakeRegisterRepository:
    def __init__(self) -> None:
        self._registers: dict[int, CashRegister] = {}

    def add(self, register: CashRegister) -> None:
        self._registers[register.id] = register

    def get_by_id(self, register_id: int) -> CashRegister | None:
        return self._registers.get(register_id)

    def get_by_terminal(self, terminal_code: str, company_id: int | None = None) -> CashRegister | None:
        return None

    def list_all(self, company_id: int | None = None) -> list[CashRegister]:
        return list(self._registers.values())


class FakeSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[int, CashSession] = {}
        self._next_id = 1

    def add(self, session: CashSession) -> None:
        session.id = self._next_id
        self._next_id += 1
        self._sessions[session.id] = session

    def save(self, session: CashSession) -> None:
        self._sessions[session.id] = session

    def get_by_id(self, session_id: int) -> CashSession | None:
        return self._sessions.get(session_id)

    def get_open_by_register(self, register_id: int) -> CashSession | None:
        for s in self._sessions.values():
            if s.register_id == register_id and s.is_open():
                return s
        return None

    def list_by_company(self, company_id: int | None = None) -> list[CashSession]:
        return list(self._sessions.values())


def test_open_session_success() -> None:
    reg_repo = FakeRegisterRepository()
    sess_repo = FakeSessionRepository()
    reg_repo.add(CashRegister(id=1, name="Caixa 1", terminal_code="T01", company_id=1))

    uc = OpenCashSession(sess_repo, reg_repo)
    output = uc.execute(
        OpenCashSessionInput(
            register_id=1,
            opening_amount_cents=10000,
            user_id=1,
            username="admin",
            company_id=1,
        )
    )

    assert output.session.id is not None
    assert output.session.is_open()
    assert output.session.opening_amount_cents == 10000


def test_open_session_one_per_register() -> None:
    reg_repo = FakeRegisterRepository()
    sess_repo = FakeSessionRepository()
    reg_repo.add(CashRegister(id=1, name="Caixa 1", terminal_code="T01", company_id=1))

    uc = OpenCashSession(sess_repo, reg_repo)
    uc.execute(
        OpenCashSessionInput(register_id=1, opening_amount_cents=0, user_id=1, username="admin")
    )

    with pytest.raises(ValidationError, match="sessão aberta"):
        uc.execute(
            OpenCashSessionInput(register_id=1, opening_amount_cents=0, user_id=1, username="admin")
        )


def test_open_session_register_not_found() -> None:
    reg_repo = FakeRegisterRepository()
    sess_repo = FakeSessionRepository()
    uc = OpenCashSession(sess_repo, reg_repo)
    with pytest.raises(NotFound):
        uc.execute(
            OpenCashSessionInput(register_id=999, opening_amount_cents=0, user_id=1, username="admin")
        )
