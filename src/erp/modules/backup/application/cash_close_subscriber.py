"""Subscriber do backup que reage a eventos de fechamento de caixa."""

from __future__ import annotations

import contextlib

from erp.modules.backup.application.service import BackupService
from erp.shared.application.events import EventBus
from erp.shared.domain.events import CashSessionClosed


class CashCloseBackupSubscriber:
    """Reage a eventos de fechamento de caixa criando backup automático."""

    def __init__(
        self,
        event_bus: EventBus,
        backup_service: BackupService,
        db_path: str,
    ) -> None:
        self._event_bus = event_bus
        self._backup_service = backup_service
        self._db_path = db_path
        self._subscribe()

    def _subscribe(self) -> None:
        self._event_bus.subscribe(CashSessionClosed, self._on_cash_session_closed)

    def _on_cash_session_closed(self, event: CashSessionClosed) -> None:
        """Cria backup automático após fechamento de caixa."""
        with contextlib.suppress(Exception):
            # Falha no backup não deve impedir o fechamento de caixa
            self._backup_service.create_backup(
                "cash_closing",
                self._db_path,
                "cash_closing",
            )
