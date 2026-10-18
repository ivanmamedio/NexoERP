"""SQLAlchemy repositories for the cash module."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from erp.modules.cash.application.ports import (
    CashMovementRepository,
    CashRegisterRepository,
    CashSessionRepository,
)
from erp.modules.cash.domain.cash_movement import CashMovement
from erp.modules.cash.domain.cash_register import CashRegister
from erp.modules.cash.domain.cash_session import CashSession
from erp.modules.cash.infrastructure.models import (
    CashMovementModel,
    CashRegisterModel,
    CashSessionModel,
)
from erp.shared.application.session import CurrentSession


class SqlAlchemyCashRegisterRepository(CashRegisterRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, register: CashRegister) -> None:
        model = CashRegisterModel()
        model.company_id = register.company_id or CurrentSession().company_id
        model.name = register.name
        model.terminal_code = register.terminal_code
        model.active = register.active
        self._session.add(model)
        self._session.flush()
        register.id = model.id

    def get_by_id(self, register_id: int) -> CashRegister | None:
        model = self._session.get(CashRegisterModel, register_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_terminal(
        self, terminal_code: str, company_id: int | None = None
    ) -> CashRegister | None:
        stmt = select(CashRegisterModel).where(CashRegisterModel.terminal_code == terminal_code)
        if company_id is not None:
            stmt = stmt.where(CashRegisterModel.company_id == company_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, company_id: int | None = None) -> list[CashRegister]:
        stmt = select(CashRegisterModel)
        cid = company_id if company_id is not None else CurrentSession().company_id
        if cid is not None:
            stmt = stmt.where(CashRegisterModel.company_id == cid)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: CashRegisterModel) -> CashRegister:
        return CashRegister(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            terminal_code=model.terminal_code,
            active=model.active,
        )


class SqlAlchemyCashSessionRepository(CashSessionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, session: CashSession) -> None:
        model = CashSessionModel()
        model.register_id = session.register_id
        model.company_id = session.company_id
        model.opened_by_user_id = session.opened_by_user_id
        model.opened_by_username = session.opened_by_username
        model.opened_at = session.opened_at  # type: ignore[assignment]
        model.opening_amount_cents = session.opening_amount_cents
        model.status = session.status
        model.closed = session.closed
        model.blind_close = session.blind_close
        self._session.add(model)
        self._session.flush()
        session.id = model.id

    def save(self, session: CashSession) -> None:
        if session.id is None:
            raise ValueError("Session must have an id to update")
        model = self._session.get(CashSessionModel, session.id)
        if model is None:
            raise ValueError(f"Session {session.id} not found")
        model.closed_by_user_id = session.closed_by_user_id
        model.closed_by_username = session.closed_by_username
        model.closed_at = session.closed_at
        model.closing_amount_cents = session.closing_amount_cents
        model.total_sales_cents = session.total_sales_cents
        model.total_suprimentos_cents = session.total_suprimentos_cents
        model.total_sangrias_cents = session.total_sangrias_cents
        model.total_pix_cents = session.total_pix_cents
        model.total_card_cents = session.total_card_cents
        model.expected_cash_cents = session.expected_cash_cents
        model.difference_cents = session.difference_cents
        model.status = session.status
        model.closed = session.closed
        model.blind_close = session.blind_close
        self._session.add(model)
        self._session.flush()

    def get_by_id(self, session_id: int) -> CashSession | None:
        model = self._session.get(CashSessionModel, session_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_open_by_register(self, register_id: int) -> CashSession | None:
        stmt = select(CashSessionModel).where(
            CashSessionModel.register_id == register_id,
            CashSessionModel.status == "open",
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(self, company_id: int | None = None) -> list[CashSession]:
        stmt = select(CashSessionModel)
        cid = company_id if company_id is not None else CurrentSession().company_id
        if cid is not None:
            stmt = stmt.where(CashSessionModel.company_id == cid)
        stmt = stmt.order_by(CashSessionModel.opened_at.desc())
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: CashSessionModel) -> CashSession:
        return CashSession(
            id=model.id,
            register_id=model.register_id,
            company_id=model.company_id,
            opened_by_user_id=model.opened_by_user_id,
            opened_by_username=model.opened_by_username,
            opened_at=model.opened_at,
            opening_amount_cents=model.opening_amount_cents,
            closed_by_user_id=model.closed_by_user_id,
            closed_by_username=model.closed_by_username,
            closed_at=model.closed_at,
            closing_amount_cents=model.closing_amount_cents,
            total_sales_cents=model.total_sales_cents,
            total_suprimentos_cents=model.total_suprimentos_cents,
            total_sangrias_cents=model.total_sangrias_cents,
            total_pix_cents=model.total_pix_cents,
            total_card_cents=model.total_card_cents,
            expected_cash_cents=model.expected_cash_cents,
            difference_cents=model.difference_cents,
            status=model.status,
            closed=model.closed,
            blind_close=model.blind_close,
        )


class SqlAlchemyCashMovementRepository(CashMovementRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, movement: CashMovement) -> None:
        model = CashMovementModel()
        model.session_id = movement.session_id
        model.company_id = movement.company_id
        model.movement_type = movement.movement_type
        model.amount_cents = movement.amount_cents
        model.description = movement.description
        model.user_id = movement.user_id
        model.username = movement.username
        model.created_at = movement.created_at  # type: ignore[assignment]
        self._session.add(model)
        self._session.flush()
        movement.id = model.id

    def list_by_session(self, session_id: int) -> list[CashMovement]:
        stmt = (
            select(CashMovementModel)
            .where(CashMovementModel.session_id == session_id)
            .order_by(CashMovementModel.created_at)
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def sum_by_session_and_type(self, session_id: int, movement_type: str) -> int:
        stmt = select(func.coalesce(func.sum(CashMovementModel.amount_cents), 0)).where(
            CashMovementModel.session_id == session_id,
            CashMovementModel.movement_type == movement_type,
        )
        return int(self._session.execute(stmt).scalar() or 0)

    @staticmethod
    def _model_to_domain(model: CashMovementModel) -> CashMovement:
        return CashMovement(
            id=model.id,
            session_id=model.session_id,
            company_id=model.company_id,
            movement_type=model.movement_type,
            amount_cents=model.amount_cents,
            description=model.description,
            user_id=model.user_id,
            username=model.username,
            created_at=model.created_at,
        )
