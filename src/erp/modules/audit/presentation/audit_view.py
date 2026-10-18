"""Audit log query view (Qt interface)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from erp.modules.audit.domain.audit_log import AuditLog


class AuditLogTableModel(QAbstractTableModel):
    """Table model for audit log entries."""

    def __init__(self, entries: list[AuditLog]) -> None:
        super().__init__()
        self._entries = entries

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        _ = parent
        return len(self._entries)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        _ = parent
        return 7

    def data(self, index: QModelIndex, role: int) -> object:  # type: ignore[override]
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        entry = self._entries[index.row()]
        column = index.column()
        if column == 0:
            return entry.created_at.strftime("%d/%m/%Y %H:%M") if entry.created_at else ""
        if column == 1:
            return entry.username or ""
        if column == 2:
            return entry.action
        if column == 3:
            return entry.entity_type
        if column == 4:
            return str(entry.entity_id) if entry.entity_id is not None else ""
        if column == 5:
            return entry.before
        if column == 6:
            return entry.after
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> object | None:  # type: ignore[override]
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (
                "Data/Hora",
                "Usuário",
                "Ação",
                "Entidade",
                "ID Entidade",
                "Antes",
                "Depois",
            )[section]
        return None


class AuditLogWidget(QWidget):
    """Consulta de log de auditoria com filtros por usuário, data e ação."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Auditoria")

        layout = QVBoxLayout(self)

        # Filter bar
        filter_bar = QHBoxLayout()
        self._user_filter = QLineEdit(self)
        self._user_filter.setPlaceholderText("Usuário")
        self._action_filter = QLineEdit(self)
        self._action_filter.setPlaceholderText("Ação")
        self._date_filter = QDateEdit(self)
        self._date_filter.setDisplayFormat("dd/MM/yyyy")
        self._btn_filter = QPushButton("Filtrar", self)
        self._btn_clear = QPushButton("Limpar", self)

        filter_bar.addWidget(self._user_filter)
        filter_bar.addWidget(self._action_filter)
        filter_bar.addWidget(self._date_filter)
        filter_bar.addWidget(self._btn_filter)
        filter_bar.addWidget(self._btn_clear)
        layout.addLayout(filter_bar)

        # Table
        self._table = QTableView(self)
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table)

        layout.setContentsMargins(8, 8, 8, 8)

    def set_entries(self, entries: list[AuditLog]) -> None:
        self._table.setModel(AuditLogTableModel(entries))
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
