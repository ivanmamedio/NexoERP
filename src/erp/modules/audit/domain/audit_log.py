"""Audit log domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class AuditLog:
    """Immutable audit trail record.

    The ``hash`` field forms a chained hash: each record includes the
    ``prev_hash`` of the previous record, so any tampering can be detected
    with :func:`verify_chain`.
    """

    id: int | None = None
    user_id: int | None = None
    username: str = ""
    action: str = ""
    entity_type: str = ""
    entity_id: int | None = None
    before: str = "{}"
    after: str = "{}"
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    prev_hash: str = ""
    hash: str = ""
