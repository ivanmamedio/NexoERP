"""Unit tests for BackupService use cases."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.backup.application.service import BackupService
from erp.modules.backup.domain import BackupStatus
from erp.modules.backup.infrastructure.models import BackupModel


class _TempDB:
    """Cria um banco SQLite temporário para testes."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.db_file = tmp_path / "test.db"
        self.engine = create_engine(f"sqlite:///{self.db_file}")
        # Create only the backup table, not all registered models
        BackupModel.__table__.create(self.engine, checkfirst=True)

    def session(self) -> Session:
        return Session(self.engine)

    def execute(self, sql: str) -> None:
        with sqlite3.connect(str(self.db_file)) as conn:
            conn.execute(sql)
            conn.commit()

    def query_count(self, sql: str) -> int:
        with sqlite3.connect(str(self.db_file)) as conn:
            return conn.execute(sql).fetchone()[0]


def test_backup_create_and_verify(tmp_path: Path) -> None:
    """Testa criar um backup e verificar sua integridade."""
    tmp_db = _TempDB(tmp_path)
    tmp_db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    tmp_db.execute("INSERT INTO test (name) VALUES ('teste')")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    service = BackupService(
        session_factory=lambda: Session(tmp_db.engine),
        backup_dir=backup_dir,
    )
    backup = service.create_backup("manual", str(tmp_db.db_file), "manual")

    assert backup.id == 1
    assert backup.status == BackupStatus.COMPLETED
    assert backup.file_path is not None
    assert backup.file_path != ""
    assert backup.checksum_sha256 != ""
    assert Path(backup.file_path).exists()

    # Verificar integridade
    assert service.verify_backup(backup.id) is True


def test_backup_corrupt_detected(tmp_path: Path) -> None:
    """Testa que corrupção de backup é detectada."""
    tmp_db = _TempDB(tmp_path)
    tmp_db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    service = BackupService(
        session_factory=lambda: Session(tmp_db.engine),
        backup_dir=backup_dir,
    )
    backup = service.create_backup("manual", str(tmp_db.db_file), "manual")
    backup_id = backup.id

    # Corromper o arquivo de backup
    with open(backup.file_path, "ab") as f:
        f.write(b"corrupted_data")

    # A verificação deve falhar
    assert service.verify_backup(backup_id) is False


def test_backup_restore_cycle(tmp_path: Path) -> None:
    """Testa ciclo completo: backup, corromper DB, restaurar, comparar."""
    tmp_db = _TempDB(tmp_path)
    tmp_db.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT)")
    tmp_db.execute("INSERT INTO products (name) VALUES ('Produto A')")
    tmp_db.execute("INSERT INTO products (name) VALUES ('Produto B')")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    service = BackupService(
        session_factory=lambda: Session(tmp_db.engine),
        backup_dir=backup_dir,
    )
    backup = service.create_backup("manual", str(tmp_db.db_file), "manual")
    assert backup.status == BackupStatus.COMPLETED

    # Corromper o banco original
    tmp_db.execute("DELETE FROM products")

    # Verificar que os dados foram perdidos
    assert tmp_db.query_count("SELECT COUNT(*) FROM products") == 0

    # Restaurar do backup
    success = service.restore_backup(backup.id, str(tmp_db.db_file))
    assert success is True

    # Verificar que os dados foram restaurados
    assert tmp_db.query_count("SELECT COUNT(*) FROM products") == 2


def test_backup_secondary_dir(tmp_path: Path) -> None:
    """Testa que backup é copiado para diretório secundário."""
    tmp_db = _TempDB(tmp_path)
    tmp_db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    backup_dir = tmp_path / "backups"
    secondary_dir = tmp_path / "secondary"
    backup_dir.mkdir()
    secondary_dir.mkdir()

    service = BackupService(
        session_factory=lambda: Session(tmp_db.engine),
        backup_dir=backup_dir,
        secondary_dir=secondary_dir,
    )
    backup = service.create_backup("manual", str(tmp_db.db_file), "manual")

    assert backup.status == BackupStatus.COMPLETED

    # Verificar que o arquivo existe no diretório secundário
    secondary_files = list(secondary_dir.iterdir())
    assert len(secondary_files) == 1
    assert secondary_files[0].name == Path(backup.file_path).name
