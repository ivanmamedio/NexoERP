"""Application ports for the audit module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.audit.domain.audit_log import AuditLog


@runtime_checkable
class AuditRepository(Protocol):
    """Port for persisting and verifying audit log entries."""

    def add(self, entry: AuditLog) -> None: ...
    def list_all(self) -> list[AuditLog]: ...
    def verify_chain(self) -> bool: ...
