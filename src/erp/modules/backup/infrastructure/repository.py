"""SQLAlchemy repository for backup entities."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from erp.modules.backup.application.ports import BackupRepositoryPort
from erp.modules.backup.domain import Backup
from erp.modules.backup.infrastructure.models import BackupModel


class SqlAlchemyBackupRepository(BackupRepositoryPort):
    """SQLAlchemy repository for backup entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, backup: Backup) -> None:
        if backup.id is None:
            self._session.execute(
                text(
                    "INSERT INTO backups "
                    "(backup_type, status, file_path, file_size_bytes, "
                    "checksum_sha256, started_at, completed_at, error_message, "
                    "source_db_path, rotation_tag) "
                    "VALUES (:backup_type, :status, :file_path, :file_size_bytes, "
                    ":checksum_sha256, :started_at, :completed_at, "
                    ":error_message, :source_db_path, :rotation_tag)"
                ),
                {
                    "backup_type": backup.backup_type,
                    "status": str(backup.status),
                    "file_path": backup.file_path,
                    "file_size_bytes": backup.file_size_bytes,
                    "checksum_sha256": backup.checksum_sha256,
                    "started_at": backup.started_at,
                    "completed_at": backup.completed_at,
                    "error_message": backup.error_message,
                    "source_db_path": backup.source_db_path,
                    "rotation_tag": backup.rotation_tag,
                },
            )
            # Obter o último id inserido (SQLite)
            row = self._session.execute(text("SELECT last_insert_rowid()")).scalar()
            backup.id = row
        else:
            self._session.execute(
                text(
                    "UPDATE backups SET "
                    "backup_type=:backup_type, status=:status, "
                    "file_path=:file_path, file_size_bytes=:file_size_bytes, "
                    "checksum_sha256=:checksum_sha256, started_at=:started_at, "
                    "completed_at=:completed_at, error_message=:error_message, "
                    "source_db_path=:source_db_path, rotation_tag=:rotation_tag "
                    "WHERE id=:id"
                ),
                {
                    "backup_type": backup.backup_type,
                    "status": str(backup.status),
                    "file_path": backup.file_path,
                    "file_size_bytes": backup.file_size_bytes,
                    "checksum_sha256": backup.checksum_sha256,
                    "started_at": backup.started_at,
                    "completed_at": backup.completed_at,
                    "error_message": backup.error_message,
                    "source_db_path": backup.source_db_path,
                    "rotation_tag": backup.rotation_tag,
                    "id": backup.id,
                },
            )
        self._session.flush()

    def get_by_id(self, backup_id: int) -> Backup | None:
        model = self._session.get(BackupModel, backup_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_type(self, backup_type: str, company_id: int | None = None) -> list[Backup]:
        stmt = select(BackupModel).where(BackupModel.backup_type == backup_type)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def list_recent(self, limit: int = 50) -> list[Backup]:
        stmt = select(BackupModel).order_by(BackupModel.started_at.desc()).limit(limit)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: BackupModel) -> Backup:
        from erp.modules.backup.domain import Backup

        backup = Backup(
            id=model.id,
            backup_type=model.backup_type,
            status=model.status,
            file_path=model.file_path,
            file_size_bytes=model.file_size_bytes,
            checksum_sha256=model.checksum_sha256,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
            source_db_path=model.source_db_path,
            rotation_tag=model.rotation_tag,
        )
        return backup
