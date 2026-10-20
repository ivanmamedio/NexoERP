"""Backup domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from erp.shared.domain.entities import Entity


class BackupType(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    PRE_MIGRATION = "pre_migration"
    CASH_CLOSING = "cash_closing"
    DAILY_FIRST_USE = "daily_first_use"
    APP_SHUTDOWN = "app_shutdown"


class BackupStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"


@dataclass(slots=True)
class Backup(Entity):
    """Backup entity with metadata."""

    backup_type: str = ""
    status: str = field(default=BackupStatus.PENDING)
    file_path: str = ""
    file_size_bytes: int = 0
    checksum_sha256: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    error_message: str = ""
    source_db_path: str = ""
    rotation_tag: str = ""  # "daily", "monthly", "manual", etc.

    def mark_in_progress(self) -> None:
        self.status = BackupStatus.IN_PROGRESS
        self.started_at = datetime.now(UTC)

    def mark_completed(self, file_path: str, file_size: int, checksum: str) -> None:
        self.status = BackupStatus.COMPLETED
        self.file_path = file_path
        self.file_size_bytes = file_size
        self.checksum_sha256 = checksum
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        self.status = BackupStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(UTC)

    @property
    def is_completed(self) -> bool:
        return self.status == BackupStatus.COMPLETED

    @property
    def duration_seconds(self) -> float | None:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None