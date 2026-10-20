"""Application ports for the backup module."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from erp.modules.backup.domain import Backup


@runtime_checkable
class BackupRepositoryPort(Protocol):
    @abstractmethod
    def add(self, backup: Backup) -> None:
        ...

    @abstractmethod
    def get_by_id(self, backup_id: int) -> Backup | None:
        ...

    @abstractmethod
    def list_by_type(
        self, backup_type: str, company_id: int | None = None
    ) -> list[Backup]:
        ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[Backup]:
        ...


@runtime_checkable
class BackupServicePort(Protocol):
    @abstractmethod
    def create_backup(
        self,
        backup_type: str,
        source_db_path: str,
        rotation_tag: str = "manual",
    ) -> Backup:
        ...

    @abstractmethod
    def restore_backup(self, backup_id: int, target_db_path: str) -> bool:
        ...

    @abstractmethod
    def verify_backup(self, backup_id: int) -> bool:
        ...

    @abstractmethod
    def rotate_backups(self) -> int:
        ...


@runtime_checkable
class SchedulerPort(Protocol):
    @abstractmethod
    def schedule_daily_backup(
        self, time_str: str, callback: Callable[[], None]
    ) -> None:
        ...

    @abstractmethod
    def schedule_monthly_backup(
        self, day: int, time_str: str, callback: Callable[[], None]
    ) -> None:
        ...

    @abstractmethod
    def cancel_scheduled(self, backup_type: str) -> None:
        ...