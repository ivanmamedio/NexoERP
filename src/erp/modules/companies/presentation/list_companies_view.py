"""View for listing companies (Qt interface)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from erp.modules.companies.application.services import CompaniesServices
from erp.modules.companies.domain.company import Company
from erp.modules.companies.presentation.create_company_view import (
    create_company_dialog,
)
from erp.modules.companies.presentation.list_companies_presenter import (
    CompaniesListPresenter,
)
from erp.shared.application.session import CurrentSession


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

        self._loading_label = QLabel("Carregando...", self)
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.hide()
        layout.addWidget(self._loading_label)

        layout.setContentsMargins(8, 8, 8, 8)

    def set_presenter(self, presenter: CompaniesListPresenter) -> None:
        self._presenter = presenter

    def set_companies(self, companies: list[Company]) -> None:
        self._table.setModel(CompanyTableModel(companies))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def show_error(self, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self, "Erro", message)

    def show_loading(self, on: bool) -> None:
        self._btn_refresh.setEnabled(not on)
        self._loading_label.setVisible(on)

    def _on_refresh(self) -> None:
        if self._presenter is not None:
            self._presenter.load()


def create_companies_list_dialog(
    services: CompaniesServices,
    session: CurrentSession,
    parent: QWidget | None = None,
) -> QDialog:
    """Factory para criar o diálogo de listagem de empresas com presenter injetado."""
    from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

    dialog = QDialog(parent)
    dialog.setWindowTitle("Empresas")
    dialog.resize(800, 600)

    layout = QVBoxLayout(dialog)

    widget = CompaniesListWidget(dialog)
    layout.addWidget(widget)

    btn_layout = QHBoxLayout()
    btn_layout.addStretch()

    btn_new = QPushButton("Nova Empresa", dialog)
    btn_close = QPushButton("Fechar", dialog)
    btn_layout.addWidget(btn_new)
    btn_layout.addWidget(btn_close)
    layout.addLayout(btn_layout)

    presenter = CompaniesListPresenter(
        view=widget,
        services=services,
        session=session,
    )
    widget.set_presenter(presenter)
    presenter.load()

    def _on_new() -> None:
        create_dialog = create_company_dialog(services, session, dialog)
        if create_dialog.exec():
            presenter.load()

    btn_new.clicked.connect(_on_new)
    btn_close.clicked.connect(dialog.reject)

    return dialog
