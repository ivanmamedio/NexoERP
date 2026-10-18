"""Audit log presenter (domain- and application-layer only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.audit.application.services import AuditService
from erp.modules.audit.domain.audit_log import AuditLog


@runtime_checkable
class AuditLogView(Protocol):
    """Contract for the audit log query screen."""

    def set_entries(self, entries: list[AuditLog]) -> None: ...


class AuditLogPresenter:
    """Orquestra a consulta do log de auditoria sem depender de Qt."""

    def __init__(self, view: AuditLogView, services: AuditService) -> None:
        self._view = view
        self._services = services

    def load(self) -> None:
        entries = self._services.list_entries()
        self._view.set_entries(entries)

    def verify_chain(self) -> bool:
        return self._services.verify_chain()
