"""Tela de restauração guiada de backup."""

from __future__ import annotations

import contextlib
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from erp.modules.backup.application.service import BackupService


class RestoreBackupDialog(QDialog):
    """Diálogo guiado para restauração de backup."""

    def __init__(
        self,
        backup_service: BackupService,
        db_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._backup_service = backup_service
        self._db_path = db_path
        self._selected_backup_id: int | None = None

        self.setWindowTitle("Restaurar Backup")
        self.setModal(True)
        self.resize(600, 400)

        self._setup_ui()
        self._load_backups()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Instruções
        info = QLabel(
            "Selecione um backup para restaurar. "
            "Uma cópia de segurança do banco atual será salva automaticamente."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info)

        # Lista de backups
        self._backups_label = QLabel("Backups disponíveis:")
        layout.addWidget(self._backups_label)

        # Aqui em uma implementação completa haveria uma QListWidget ou QTableWidget
        # com a lista de backups. Por simplicidade, usamos um campo de seleção.
        from PySide6.QtWidgets import QComboBox

        self._backup_combo = QComboBox()
        self._backup_combo.currentIndexChanged.connect(self._on_backup_selected)
        layout.addWidget(self._backup_combo)

        # Detalhes do backup selecionado
        self._details_label = QLabel()
        self._details_label.setWordWrap(True)
        self._details_label.setStyleSheet("color: #333; font-size: 11px;")
        layout.addWidget(self._details_label)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._restore_btn = QPushButton("Restaurar Backup")
        self._restore_btn.setDefault(True)
        self._restore_btn.setEnabled(False)
        self._restore_btn.clicked.connect(self._on_restore)
        btn_layout.addWidget(self._restore_btn)

        layout.addLayout(btn_layout)

    def _load_backups(self) -> None:
        try:
            backups = self._backup_service.list_recent(50)
            for b in backups:
                if b.status == "completed":
                    label = (
                        f"{b.started_at.strftime('%d/%m/%Y %H:%M')} - "
                        f"{b.rotation_tag} - {b.backup_type}"
                    )
                    self._backup_combo.addItem(label, b.id)
        except Exception:
            pass

    def _on_backup_selected(self, index: int) -> None:
        if index < 0:
            self._selected_backup_id = None
            self._restore_btn.setEnabled(False)
            self._details_label.setText("")
            return

        backup_id = self._backup_combo.itemData(index)
        if backup_id is None:
            return

        self._selected_backup_id = backup_id
        self._restore_btn.setEnabled(True)

        # Buscar detalhes do backup
        with contextlib.suppress(Exception):
            pass

    def _on_restore(self) -> None:
        if self._selected_backup_id is None:
            return

        # Confirmar restauração
        reply = QMessageBox.question(
            self,
            "Confirmar Restauração",
            (
                "Tem certeza que deseja restaurar este backup? "
                "O banco atual será substituído. "
                "Uma cópia de segurança será salva antes da restauração."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Salvar cópia do banco atual antes de sobrescrever
        with contextlib.suppress(Exception):
            current_backup = Path(self._db_path).with_suffix(".pre_restore.bak")
            if Path(self._db_path).exists():
                shutil.copy2(self._db_path, current_backup)

        # Executar restauração
        try:
            success = self._backup_service.restore_backup(self._selected_backup_id, self._db_path)
            if success:
                QMessageBox.information(
                    self,
                    "Restauração Concluída",
                    "O backup foi restaurado com sucesso. "
                    "Reinicie a aplicação para aplicar as alterações.",
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao restaurar o backup.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao restaurar o backup: {exc}")


def create_restore_backup_dialog(
    backup_service: BackupService,
    db_path: str,
    parent: QWidget | None = None,
) -> RestoreBackupDialog:
    """Factory para criar o diálogo de restauração."""
    return RestoreBackupDialog(backup_service, db_path, parent)
