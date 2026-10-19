"""SQLAlchemy repository for audit log entries."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.audit.application.ports import AuditRepository
from erp.modules.audit.domain.audit_log import AuditLog
from erp.modules.audit.infrastructure.models import AuditLogModel


class SqlAlchemyAuditRepository(AuditRepository):
    """SQLAlchemy implementation of AuditRepository.

    The table is append-only: entries are never updated or deleted once
    written, which is enforced by SQLite triggers (see infrastructure/triggers.py).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: AuditLog) -> None:
        model = AuditLogModel()
        model.user_id = entry.user_id
        model.username = entry.username
        model.action = entry.action
        model.entity_type = entry.entity_type
        model.entity_id = entry.entity_id
        model.before = entry.before
        model.after = entry.after
        model.created_at = entry.created_at if entry.created_at is not None else datetime.now(UTC)
        model.prev_hash = entry.prev_hash
        model.hash = entry.hash

        self._session.add(model)
        self._session.flush()
        entry.id = model.id

    def list_all(self, *, company_id: int | None = None) -> list[AuditLog]:
        # Audit logs are not scoped by company in the current schema
        stmt = select(AuditLogModel).order_by(AuditLogModel.id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity.

        Returns True if every record's hash is correct and each record's
        ``prev_hash`` matches the previous record's hash.
        """
        entries = self.list_all()
        expected_prev = "0" * 64
        for entry in entries:
            expected_hash = self._compute_hash(entry, expected_prev)
            if entry.hash != expected_hash:
                return False
            expected_prev = entry.hash
        return True

    @staticmethod
    def _compute_hash(entry: AuditLog, prev_hash: str) -> str:
        created_at = entry.created_at.isoformat() if entry.created_at else ""
        payload = (
            f"{prev_hash}|{entry.user_id}|{entry.username}|"
            f"{entry.action}|{entry.entity_type}|{entry.entity_id}|"
            f"{entry.before}|{entry.after}|{created_at}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _model_to_domain(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            user_id=model.user_id,
            username=model.username,
            action=model.action,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            before=model.before,
            after=model.after,
            created_at=model.created_at,
            prev_hash=model.prev_hash,
            hash=model.hash,
        )
