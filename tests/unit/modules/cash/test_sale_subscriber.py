"""Unit tests for CashSaleSubscriber."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.cash.application.sale_subscriber import CashSaleSubscriber
from erp.modules.cash.domain.cash_movement import MovementType
from erp.modules.cash.infrastructure.models import (
    Base,
    CashMovementModel,
    CashSessionModel,
)
from erp.modules.sales.infrastructure.models import SaleModel
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


def _create_tables(session: Session) -> None:
    Base.metadata.create_all(session.get_bind())


def _insert_cash_session(
    session: Session, session_id: int, status: str = "open"
) -> None:
    session.execute(
        CashSessionModel.__table__.insert(),
        [
            {
                "id": session_id,
                "register_id": 1,
                "company_id": 1,
                "opened_by_user_id": 1,
                "opened_by_username": "caixa",
                "opened_at": datetime.now(UTC),
                "opening_amount_cents": 10000,
                "status": status,
                "closed": False,
                "total_sales_cents": 0,
                "total_pix_cents": 0,
                "total_card_cents": 0,
            }
        ],
    )


def _insert_sale(session: Session, sale_id: int) -> None:
    session.execute(
        SaleModel.__table__.insert(),
        [
            {
                "id": sale_id,
                "company_id": 1,
                "session_id": 1,
                "status": "finalized",
                "subtotal_cents": 5000,
                "discount_cents": 0,
                "total_cents": 5000,
                "paid_cents": 5000,
                "change_cents": 0,
                "username": "caixa",
                "created_at": datetime.now(UTC),
            }
        ],
    )


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_cash_sale_subscriber_records_cash_movement(engine) -> None:
    with Session(engine) as session:
        _insert_cash_session(session, 1)
        _insert_sale(session, 1)
        session.commit()

    event_bus = EventBus()
    CashSaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=1,
        company_id=1,
        session_id=1,
        user_id=1,
        username="caixa",
        total_cents=5000,
        cash_cents=5000,
        pix_cents=0,
        card_cents=0,
    )
    event_bus.publish(event)

    with Session(engine) as session:
        movements = (
            session.query(CashMovementModel)
            .filter_by(session_id=1, movement_type=MovementType.VENDA_DINHEIRO)
            .all()
        )
        assert len(movements) == 1
        assert movements[0].amount_cents == 5000

        # Session totals updated
        from erp.modules.cash.infrastructure.models import CashSessionModel as CSM

        sess = session.get(CSM, 1)
        assert sess is not None
        assert sess.total_sales_cents == 5000


def test_cash_sale_subscriber_no_session_skips(engine) -> None:
    event_bus = EventBus()
    CashSaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=1,
        company_id=1,
        session_id=None,
        user_id=1,
        username="caixa",
        total_cents=5000,
        cash_cents=5000,
        pix_cents=0,
        card_cents=0,
    )
    # Should not raise even with no session
    event_bus.publish(event)

    with Session(engine) as session:
        movements = session.query(CashMovementModel).all()
        assert len(movements) == 0


def test_cash_sale_subscriber_records_pix_and_card_totals(engine) -> None:
    with Session(engine) as session:
        _insert_cash_session(session, 1)
        _insert_sale(session, 1)
        session.commit()

    event_bus = EventBus()
    CashSaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=1,
        company_id=1,
        session_id=1,
        user_id=1,
        username="caixa",
        total_cents=5000,
        cash_cents=3000,
        pix_cents=1000,
        card_cents=1000,
    )
    event_bus.publish(event)

    with Session(engine) as session:
        from erp.modules.cash.infrastructure.models import CashSessionModel as CSM

        sess = session.get(CSM, 1)
        assert sess is not None
        assert sess.total_sales_cents == 3000
        assert sess.total_pix_cents == 1000
        assert sess.total_card_cents == 1000

        # Only cash creates a movement
        movements = session.query(CashMovementModel).all()
        assert len(movements) == 1
        assert movements[0].amount_cents == 3000
