"""Backup service implementation."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from erp.modules.backup.application.ports import BackupRepositoryPort, BackupServicePort
from erp.modules.backup.domain import Backup, BackupStatus


class BackupService(BackupServicePort):
    """Backup service using sqlite3 backup API with zip and SHA-256."""

    def __init__(
        self,
        repo: BackupRepositoryPort,
        backup_dir: Path,
        secondary_dir: Path | None = None,
        max_daily: int = 30,
        max_monthly: int = 12,
    ) -> None:
        self._repo = repo
        self._backup_dir = backup_dir
        self._secondary_dir = secondary_dir
        self._max_daily = max_daily
        self._max_monthly = max_monthly
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        if self._secondary_dir:
            self._secondary_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        backup_type: str,
        source_db_path: str,
        rotation_tag: str = "manual",
    ) -> Backup:
        backup = Backup(
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            source_db_path=source_db_path,
            rotation_tag=rotation_tag,
        )
        self._repo.add(backup)

        try:
            backup.mark_in_progress()
            # repo.add() flushes and sets the id
            file_path = self._perform_backup(source_db_path, backup.id, rotation_tag)  # type: ignore[arg-type]
            file_size = Path(file_path).stat().st_size
            checksum = self._calculate_checksum(file_path)
            backup.mark_completed(file_path, file_size, checksum)

            # Copy to secondary location if configured
            if self._secondary_dir:
                shutil.copy2(file_path, self._secondary_dir / Path(file_path).name)

            self.rotate_backups()
            self._repo.add(backup)  # Update with completed info
            return backup

        except Exception as exc:
            backup.mark_failed(str(exc))
            raise

    def _perform_backup(self, source_db: str, backup_id: int, rotation_tag: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{backup_id}_{timestamp}_{source_db.split('/')[-1]}.zip"
        zip_path = self._backup_dir / filename

        with (
            sqlite3.connect(source_db) as src_conn,
            zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf,
        ):
            # Create backup using sqlite3 backup API
            backup_conn = sqlite3.connect(":memory:")
            src_conn.backup(backup_conn)
            backup_conn.close()

            # Write the backup to zip
            with sqlite3.connect(":memory:") as mem_conn:
                src_conn.backup(mem_conn)
                # Write the database dump to zip
                dump = "".join(mem_conn.iterdump())
                zipf.writestr("database.sql", dump)

        return str(zip_path)

    def _calculate_checksum(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def restore_backup(self, backup_id: int, target_db_path: str) -> bool:
        backup = self._repo.get_by_id(backup_id)
        if backup is None:
            raise ValueError(f"Backup {backup_id} not found")
        if backup.status != BackupStatus.COMPLETED:
            raise ValueError(f"Backup {backup_id} is not completed")

        # Verify checksum
        if not self.verify_backup(backup.id):  # type: ignore[arg-type]
            raise ValueError(f"Backup {backup_id} checksum mismatch")

        # Create a copy of current DB before restore
        current_backup_path = Path(target_db_path).with_suffix(".pre_restore.bak")
        if Path(target_db_path).exists():
            shutil.copy2(target_db_path, current_backup_path)

        # Extract and restore
        with zipfile.ZipFile(backup.file_path, "r") as zipf:
            dump = zipf.read("database.sql").decode("utf-8")
            with open(target_db_path + ".sql", "w") as f:
                f.write(dump)

        # Execute SQL dump to restore
        with (
            sqlite3.connect(target_db_path) as conn,
            zipfile.ZipFile(backup.file_path, "r") as zipf,
        ):
            dump = zipf.read("database.sql").decode("utf-8")
            conn.executescript(dump)

        return True

    def verify_backup(self, backup_id: int) -> bool:
        backup = self._repo.get_by_id(backup_id)
        if backup is None or backup.status != "completed":
            return False

        if not Path(backup.file_path).exists():
            backup.mark_failed("File not found")
            return False

        actual_checksum = self._calculate_checksum(backup.file_path)
        if actual_checksum != backup.checksum_sha256:
            backup.mark_failed("Checksum mismatch")
            return False

        # Quick integrity check by trying to read the zip
        try:
            with zipfile.ZipFile(backup.file_path, "r") as zipf:
                zipf.testzip()
        except zipfile.BadZipFile:
            backup.mark_failed("Corrupted zip file")
            return False

        return True

    def rotate_backups(self) -> int:
        """Rotate backups: keep N daily + N monthly."""
        removed = 0

        # Group by date and rotation tag
        all_backups = self._repo.list_recent(1000)
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

        return removed

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
