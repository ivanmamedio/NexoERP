"""Integration tests for the audit repository using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.audit.application.services import AuditService
from erp.modules.audit.domain.audit_log import AuditLog
from erp.modules.audit.infrastructure.models import AuditLogModel
from erp.modules.audit.infrastructure.repository import SqlAlchemyAuditRepository
from erp.shared.infrastructure.database import Base


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def _make_entry(
    action: str = "company.create",
    username: str = "admin",
    prev_hash: str = "0" * 64,
) -> AuditLog:
    return AuditLog(
        user_id=1,
        username=username,
        action=action,
        entity_type="Company",
        entity_id=1,
        before="{}",
        after='{"name": "ACME"}',
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        prev_hash=prev_hash,
    )


def test_append_and_list(session: Session) -> None:
    repo = SqlAlchemyAuditRepository(session)

    entry1 = _make_entry(action="company.create")
    entry1.hash = AuditService._compute_hash(entry1, entry1.prev_hash)
    repo.add(entry1)

    entry2 = _make_entry(action="company.update", prev_hash=entry1.hash)
    entry2.hash = AuditService._compute_hash(entry2, entry1.hash)
    repo.add(entry2)

    entries = repo.list_all()
    assert len(entries) == 2
    assert entries[0].action == "company.create"
    assert entries[1].action == "company.update"
    assert entries[1].prev_hash == entries[0].hash


def test_verify_chain_valid(session: Session) -> None:
    repo = SqlAlchemyAuditRepository(session)

    entry1 = _make_entry(action="company.create")
    entry1.hash = AuditService._compute_hash(entry1, entry1.prev_hash)
    repo.add(entry1)

    entry2 = _make_entry(action="company.update", prev_hash=entry1.hash)
    entry2.hash = AuditService._compute_hash(entry2, entry1.hash)
    repo.add(entry2)

    assert repo.verify_chain() is True


def test_verify_chain_detects_tampering(session: Session) -> None:
    repo = SqlAlchemyAuditRepository(session)

    entry1 = _make_entry(action="company.create")
    entry1.hash = AuditService._compute_hash(entry1, entry1.prev_hash)
    repo.add(entry1)

    entry2 = _make_entry(action="company.update", prev_hash=entry1.hash)
    entry2.hash = AuditService._compute_hash(entry2, entry1.hash)
    repo.add(entry2)

    # Tamper directly with the model
    model = session.get(AuditLogModel, entry1.id)
    assert model is not None
    model.after = '{"name": "TAMPERED"}'
    session.commit()

    assert repo.verify_chain() is False
