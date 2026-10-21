"""Backup settings dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from erp.modules.backup.application.service import BackupService
    from erp.modules.backup.infrastructure.scheduler import BackupScheduler


class BackupSettingsDialog(QDialog):
    """Dialog for configuring backup settings."""

    def __init__(
        self,
        backup_service: BackupService,
        scheduler: BackupScheduler,
        current_settings: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._backup_service = backup_service
        self._scheduler = scheduler
        self._settings = current_settings.copy()

        self.setWindowTitle("Configurações de Backup")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Backup directory
        self._backup_dir_edit = QLabel()
        self._backup_dir_edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Diretório de backup:", self._backup_dir_edit)

        browse_btn = QPushButton("Alterar...")
        browse_btn.clicked.connect(self._browse_backup_dir)
        form.addRow("", browse_btn)

        # Secondary backup directory
        self._secondary_dir_edit = QLabel()
        self._secondary_dir_edit.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        form.addRow("Diretório secundário:", self._secondary_dir_edit)

        secondary_browse = QPushButton("Alterar...")
        secondary_browse.clicked.connect(self._browse_secondary_dir)
        form.addRow("", secondary_browse)

        # Daily backups retention
        self._daily_spin = QSpinBox()
        self._daily_spin.setRange(1, 365)
        self._daily_spin.setValue(30)
        form.addRow("Retenção diária (dias):", self._daily_spin)

        # Monthly backups retention
        self._monthly_spin = QSpinBox()
        self._monthly_spin.setRange(1, 60)
        self._monthly_spin.setValue(12)
        form.addRow("Retenção mensal (meses):", self._monthly_spin)

        # Scheduled backups - daily time
        self._daily_hour_spin = QSpinBox()
        self._daily_hour_spin.setRange(0, 23)
        form.addRow("Horário backup diário (hora):", self._daily_hour_spin)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        test_btn = QPushButton("Testar Backup Agora")
        test_btn.clicked.connect(self._on_test_backup)
        btn_layout.addWidget(test_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _browse_backup_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar diretório de backup")
        if dir_path:
            self._backup_dir_edit.setText(dir_path)
            self._settings["backup_dir"] = dir_path

    def _browse_secondary_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar diretório secundário")
        if dir_path:
            self._secondary_dir_edit.setText(dir_path)
            self._settings["secondary_dir"] = dir_path

    def _on_test_backup(self) -> None:
        QMessageBox.information(
            self, "Teste", "Funcionalidade de teste de backup a ser implementada."
        )

    def _load_settings(self) -> None:
        # Load from settings dict
        pass

    def _on_save(self) -> None:
        self.accept()

    def get_settings(self) -> dict[str, str]:
        return self._settings


def create_backup_settings_dialog(
    backup_service: BackupService,
    scheduler: BackupScheduler,
    current_settings: dict[str, str],
    parent: QWidget | None = None,
) -> BackupSettingsDialog:
    return BackupSettingsDialog(backup_service, scheduler, current_settings, parent)
