"""Backup service implementation."""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import tempfile
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from erp.modules.backup.application.ports import BackupServicePort
from erp.modules.backup.domain import Backup, BackupStatus
from erp.modules.backup.infrastructure.repository import SqlAlchemyBackupRepository


class BackupService(BackupServicePort):
    """Backup service using sqlite3 Connection.backup() API with zip and SHA-256."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        backup_dir: Path,
        secondary_dir: Path | None = None,
        max_daily: int = 30,
        max_monthly: int = 12,
    ) -> None:
        self._session_factory = session_factory
        self._backup_dir = backup_dir
        self._secondary_dir = secondary_dir
        self._max_daily = max_daily
        self._max_monthly = max_monthly
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        if self._secondary_dir:
            self._secondary_dir.mkdir(parents=True, exist_ok=True)

    def _new_repo(self) -> SqlAlchemyBackupRepository:
        return SqlAlchemyBackupRepository(self._session_factory())

    def create_backup(
        self,
        backup_type: str,
        source_db_path: str,
        rotation_tag: str = "manual",
    ) -> Backup:
        session = self._session_factory()
        try:
            repo = SqlAlchemyBackupRepository(session)
            backup = Backup(
                backup_type=backup_type,
                status=BackupStatus.PENDING,
                source_db_path=source_db_path,
                rotation_tag=rotation_tag,
            )
            repo.add(backup)

            try:
                backup.mark_in_progress()
                # repo.add() flushes and sets the id
                file_path = self._perform_backup(source_db_path, backup.id, rotation_tag)  # type: ignore[arg-type]
                file_size = Path(file_path).stat().st_size
                checksum = self._calculate_checksum(file_path)
                backup.mark_completed(file_path, file_size, checksum)
                repo.add(backup)  # Atualiza registro com file_path, checksum, etc.

                # Copy to secondary location if configured
                if self._secondary_dir:
                    shutil.copy2(file_path, self._secondary_dir / Path(file_path).name)

                self.rotate_backups()
                session.commit()
                return backup

            except Exception as exc:
                session.rollback()
                backup.mark_failed(str(exc))
                raise
        finally:
            session.close()

    def _perform_backup(self, source_db: str, backup_id: int, rotation_tag: str) -> str:
        """Create a backup using sqlite3.Connection.backup() API.

        The backup is written to a temporary SQLite file, then compressed
        into a ZIP archive with SHA-256 checksum.
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_db).name
        filename = f"backup_{backup_id}_{timestamp}_{source_name}.zip"
        zip_path = self._backup_dir / filename

        # PRAGMA integrity_check on source database before backup
        src_conn = sqlite3.connect(source_db)
        try:
            src_conn.execute("PRAGMA integrity_check")
            src_conn.execute("PRAGMA foreign_keys=ON")
        finally:
            src_conn.close()

        # Create backup using sqlite3.Connection.backup() to a temp file
        with tempfile.NamedTemporaryFile(
            suffix=".db", delete=False, dir=str(self._backup_dir)
        ) as tmp_file:
            tmp_path = tmp_file.name

        try:
            src_conn = sqlite3.connect(source_db)
            dst_conn = sqlite3.connect(tmp_path)
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()

            # Compress the backup into a ZIP archive
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(tmp_path, arcname=source_name)

            return str(zip_path)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _calculate_checksum(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def restore_backup(self, backup_id: int, target_db_path: str) -> bool:
        session = self._session_factory()
        try:
            repo = SqlAlchemyBackupRepository(session)
            backup = repo.get_by_id(backup_id)
            if backup is None:
                raise ValueError(f"Backup {backup_id} not found")

            # Verify checksum before restore
            if not self.verify_backup(backup.id):  # type: ignore[arg-type]
                raise ValueError(f"Backup {backup_id} checksum mismatch")

            # Create a copy of current DB before restore (safety)
            current_backup_path = Path(target_db_path).with_suffix(".pre_restore.bak")
            if Path(target_db_path).exists():
                shutil.copy2(target_db_path, current_backup_path)

            # Extract the SQLite file from the ZIP and copy to target
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
                    tmp_path = tmp_file.name

                with zipfile.ZipFile(backup.file_path, "r") as zipf:
                    # Find the database file in the zip (first .db file)
                    db_name = None
                    for name in zipf.namelist():
                        if name.endswith(".db"):
                            db_name = name
                            break
                    if db_name is None:
                        raise ValueError("No database file found in backup zip")
                    zipf.extract(db_name, path=str(Path(tmp_path).parent))
                    extracted_path = Path(Path(tmp_path).parent) / db_name
                    shutil.copy2(str(extracted_path), tmp_path)
                    # Clean up extracted file
                    if extracted_path.exists():
                        os.unlink(str(extracted_path))

                # Copy the extracted backup to the target location
                shutil.copy2(tmp_path, target_db_path)

                return True
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        finally:
            session.close()

    def verify_backup(self, backup_id: int) -> bool:
        session = self._session_factory()
        try:
            repo = SqlAlchemyBackupRepository(session)
            backup = repo.get_by_id(backup_id)
            if backup is None:
                return False

            if not Path(backup.file_path).exists():
                return False

            actual_checksum = self._calculate_checksum(backup.file_path)
            if actual_checksum != backup.checksum_sha256:
                return False

            # Quick integrity check by trying to read the zip
            try:
                with zipfile.ZipFile(backup.file_path, "r") as zipf:
                    zipf.testzip()
            except zipfile.BadZipFile:
                return False

            return True
        finally:
            session.close()

    def list_recent(self, limit: int = 50) -> list[Backup]:
        """Lista os backups mais recentes."""
        session = self._session_factory()
        try:
            repo = SqlAlchemyBackupRepository(session)
            return repo.list_recent(limit)
        finally:
            session.close()

    def rotate_backups(self) -> int:
        """Rotate backups: keep N daily + N monthly."""
        session = self._session_factory()
        try:
            repo = SqlAlchemyBackupRepository(session)
            removed = 0

            # Group by date and rotation tag
            all_backups = repo.list_recent(1000)
            daily_backups = [b for b in all_backups if b.rotation_tag == "daily"]
            monthly_backups = [b for b in all_backups if b.rotation_tag == "monthly"]

            # Sort by date (oldest first)
            daily_backups.sort(key=lambda b: b.started_at)
            monthly_backups.sort(key=lambda b: b.started_at)

            # Remove excess daily
            for backup in daily_backups[: -self._max_daily]:
                self._delete_backup(backup)
                removed += 1

            # Remove excess monthly
            for backup in monthly_backups[: -self._max_monthly]:
                self._delete_backup(backup)
                removed += 1

            session.commit()
            return removed
        finally:
            session.close()

    def _delete_backup(self, backup: Backup) -> None:
        try:
            if backup.file_path and Path(backup.file_path).exists():
                Path(backup.file_path).unlink()
            if self._secondary_dir:
                secondary_path = self._secondary_dir / Path(backup.file_path).name
                if secondary_path.exists():
                    secondary_path.unlink()
        except OSError:
            pass  # Log error but don't fail rotation
