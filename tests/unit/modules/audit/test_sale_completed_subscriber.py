"""Unit tests for AuditEventSubscriber reacting to SaleCompleted."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.audit.application.event_subscriber import AuditEventSubscriber
from erp.modules.audit.application.services import AuditService
from erp.modules.audit.infrastructure.models import AuditLogModel, Base
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_audit_subscriber_records_sale_completed(engine) -> None:
    event_bus = EventBus()
    audit_service = AuditService(engine)
    AuditEventSubscriber(event_bus=event_bus, audit_service=audit_service)

    event = SaleCompleted(
        sale_id=42,
        company_id=1,
        session_id=1,
        user_id=7,
        username="caixa",
        total_cents=5000,
        cash_cents=3000,
        pix_cents=1000,
        card_cents=1000,
    )
    event_bus.publish(event)

    with Session(engine) as session:
        logs = session.query(AuditLogModel).filter_by(action="sale.completed").all()
        assert len(logs) == 1
        log = logs[0]
        assert log.entity_type == "Sale"
        assert log.entity_id == 42
        assert log.user_id == 7
        assert log.username == "caixa"
        after = json.loads(log.after)
        assert after["total_cents"] == 5000
        assert after["cash_cents"] == 3000


def test_audit_subscriber_verify_chain_after_sale(engine) -> None:
    event_bus = EventBus()
    audit_service = AuditService(engine)
    AuditEventSubscriber(event_bus=event_bus, audit_service=audit_service)

    # Publish multiple SaleCompleted events
    for i in range(3):
        event = SaleCompleted(
            sale_id=100 + i,
            company_id=1,
            session_id=None,
            user_id=1,
            username="caixa",
            total_cents=1000 * (i + 1),
            cash_cents=1000 * (i + 1),
            pix_cents=0,
            card_cents=0,
        )
        event_bus.publish(event)

    assert audit_service.verify_chain() is True
