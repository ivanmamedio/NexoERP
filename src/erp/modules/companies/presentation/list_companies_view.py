"""View for listing companies (Qt interface)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from erp.modules.companies.domain.company import Company
from erp.modules.companies.presentation.list_companies_presenter import (
    CompaniesListPresenter,
)


class CompanyTableModel(QAbstractTableModel):
    """Modelo simplificado para a tabela de empresas."""

    def __init__(self, companies: list[Company]) -> None:
        super().__init__()
        self._companies = companies

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        _ = parent
        return len(self._companies)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        _ = parent
        return 4

    def data(self, index: QModelIndex, role: int) -> object:  # type: ignore[override]
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        row = index.row()
        column = index.column()
        company = self._companies[row]
        if column == 0:
            return company.name
        if column == 1:
            return company.trade_name
        if column == 2:
            return company.tax_id
        if column == 3:
            return "Sim" if company.active else "Não"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> object | None:  # type: ignore[override]
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return ("Razão social", "Nome fantasia", "CNPJ", "Ativa")[section]
        return None


class CompaniesListWidget(QWidget):
    """Exibe a lista de empresas e dispõe os controles."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: CompaniesListPresenter | None = None

        self.setWindowTitle("Empresas")
        layout = QVBoxLayout(self)

        self._table = QTableView(self)
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table)

        self._btn_refresh = QPushButton("Atualizar", self)
        self._btn_refresh.clicked.connect(self._on_refresh)
        layout.addWidget(self._btn_refresh)

        layout.setContentsMargins(8, 8, 8, 8)

    def set_presenter(self, presenter: CompaniesListPresenter) -> None:
        self._presenter = presenter

    def set_companies(self, companies: list[Company]) -> None:
        self._table.setModel(CompanyTableModel(companies))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _on_refresh(self) -> None:
        if self._presenter is not None:
            self._presenter.load()
