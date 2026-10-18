"""Application services facade for the audit module."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy.engine import Engine

from erp.modules.audit.domain.audit_log import AuditLog
from erp.modules.audit.infrastructure.unit_of_work import (
    SqlAlchemyAuditUnitOfWork,
)


class AuditService:
    """Facade over audit log use cases (one transaction per operation)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def log_event(
        self,
        *,
        user_id: int | None,
        username: str,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        before: dict[str, object] | None = None,
        after: dict[str, object] | None = None,
    ) -> AuditLog:
        """Append a new chained audit log entry."""
        with SqlAlchemyAuditUnitOfWork(self._engine) as uow:
            assert uow.audit_logs is not None
            previous = uow.audit_logs.list_all()
            prev_hash = previous[-1].hash if previous else "0" * 64

            entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                before=json.dumps(before or {}, sort_keys=True),
                after=json.dumps(after or {}, sort_keys=True),
                created_at=datetime.now(UTC),
                prev_hash=prev_hash,
            )
            entry.hash = self._compute_hash(entry)
            uow.audit_logs.add(entry)
            uow.commit()
            return entry

    def list_entries(self) -> list[AuditLog]:
        """Return all audit log entries ordered by creation time."""
        with SqlAlchemyAuditUnitOfWork(self._engine) as uow:
            assert uow.audit_logs is not None
            return uow.audit_logs.list_all()

    def verify_chain(self) -> bool:
        """Return True if the hash chain is intact, False if tampered."""
        with SqlAlchemyAuditUnitOfWork(self._engine) as uow:
            assert uow.audit_logs is not None
            return uow.audit_logs.verify_chain()

    @staticmethod
    def _compute_hash(entry: AuditLog, prev_hash: str | None = None) -> str:
        effective_prev = prev_hash if prev_hash is not None else entry.prev_hash
        created_at = entry.created_at.isoformat() if entry.created_at else ""
        payload = (
            f"{effective_prev}|{entry.user_id}|{entry.username}|"
            f"{entry.action}|{entry.entity_type}|{entry.entity_id}|"
            f"{entry.before}|{entry.after}|{created_at}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
