"""Company selection dialog after login."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from erp.modules.identity.presentation.select_company_presenter import (
        SelectCompanyPresenter,
    )


@runtime_checkable
class SelectCompanyView(Protocol):
    """Contrato da tela de seleção de empresa consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def render_companies(self, companies: list[tuple[int, str]]) -> None: ...
    def get_selected_company_id(self) -> int | None: ...
    def accept(self) -> None: ...


class SelectCompanyDialog(QDialog):
    """Janela modal para seleção da empresa após login."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: SelectCompanyPresenter | None = None

        self.setWindowTitle("NexoERP — Selecionar Empresa")
        self.setModal(True)
        self.setMinimumSize(400, 350)
        self.setObjectName("SelectCompanyDialog")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        # Header
        title = QLabel("Selecionar Empresa", self)
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(title)

        subtitle = QLabel(
            "Escolha a empresa para acessar o sistema:",
            self,
        )
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        root_layout.addWidget(subtitle)

        # List of companies
        self._list = QListWidget(self)
        self._list.setObjectName("CompanyList")
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        root_layout.addWidget(self._list, stretch=1)

        # Buttons
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        self._buttons.setObjectName("SelectButtons")
        ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setObjectName("SelectButton")
            ok_button.setText("Entrar")
            ok_button.setDefault(True)

        cancel_button = self._buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setObjectName("CancelButton")
            cancel_button.setText("Cancelar")

        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        root_layout.addWidget(self._buttons, alignment=Qt.AlignmentFlag.AlignCenter)

    # --- SelectCompanyView protocol ---------------------------------------

    def set_presenter(self, presenter: SelectCompanyPresenter) -> None:
        self._presenter = presenter

    def show_error(self, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Erro", message)

    def show_info(self, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Informação", message)

    def render_companies(self, companies: list[tuple[int, str]]) -> None:
        """Renderiza a lista de empresas disponíveis.
        
        Args:
            companies: Lista de tuplas (company_id, company_name)
        """
        self._list.clear()
        for company_id, name in companies:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, company_id)
            self._list.addItem(item)
        
        if companies:
            self._list.setCurrentRow(0)

    def get_selected_company_id(self) -> int | None:
        item = self._list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def accept(self) -> None:
        if self._presenter is not None:
            company_id = self.get_selected_company_id()
            if company_id is not None:
                self._presenter.select_company(company_id)
            else:
                self.show_error("Selecione uma empresa.")
        else:
            super().accept()

    # --- internals ----------------------------------------------------------

    def _on_accept(self) -> None:
        if self._presenter is not None:
            company_id = self.get_selected_company_id()
            if company_id is not None:
                self._presenter.select_company(company_id)
            else:
                self.show_error("Selecione uma empresa.")
        else:
            super().accept()


def create_select_company_dialog(
    presenter: SelectCompanyPresenter,
    parent: QWidget | None = None,
) -> SelectCompanyDialog:
    dialog = SelectCompanyDialog(parent)
    dialog.set_presenter(presenter)
    return dialog