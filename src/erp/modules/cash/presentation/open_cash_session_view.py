"""Qt view for opening cash session."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.cash.application.services import CashServices
from erp.modules.cash.presentation.open_cash_session_presenter import (
    OpenCashSessionPresenter,
    OpenCashSessionView,
)
from erp.shared.application.session import CurrentSession


class OpenCashSessionDialog(QDialog, OpenCashSessionView):
    """Diálogo para abrir sessão de caixa."""

    def __init__(
        self,
        presenter: OpenCashSessionPresenter | None,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session

        self.setWindowTitle("Abrir Sessão de Caixa")
        self.setModal(True)
        self.resize(400, 200)

        self._setup_ui()
        if self._presenter is not None:
            self._presenter.load_registers()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._register_combo = QComboBox()
        self._register_combo.setPlaceholderText("Selecione um caixa")
        form.addRow("Caixa:", self._register_combo)

        self._amount_spin = QSpinBox()
        self._amount_spin.setRange(0, 99999999)
        self._amount_spin.setSuffix(" centavos")
        self._amount_spin.setGroupSeparatorShown(True)
        form.addRow("Valor de abertura (centavos):", self._amount_spin)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._open_btn = QPushButton("Abrir Sessão")
        self._open_btn.setDefault(True)
        self._open_btn.clicked.connect(self._on_open_clicked)
        btn_layout.addWidget(self._open_btn)

        layout.addLayout(btn_layout)

    def _on_open_clicked(self) -> None:
        if self._presenter is not None and self._presenter.open_session():
            self.accept()

    # --- OpenCashSessionView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def show_success(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)

    def set_registers(self, registers: list[tuple[int, str]]) -> None:
        self._register_combo.clear()
        for reg_id, terminal_code in registers:
            self._register_combo.addItem(terminal_code, reg_id)

    def get_selected_register_id(self) -> int | None:
        idx = self._register_combo.currentIndex()
        if idx < 0:
            return None
        data = self._register_combo.itemData(idx)
        return data if isinstance(data, int) else None

    def get_opening_amount_cents(self) -> int:
        return self._amount_spin.value()

    def accept(self) -> None:
        super().accept()


def create_open_cash_session_dialog(
    services: CashServices,
    session: CurrentSession,
    engine: Engine,
    parent: QWidget | None = None,
) -> OpenCashSessionDialog:
    """Factory para criar o diálogo com presenter injetado."""
    dialog = OpenCashSessionDialog(None, session, parent)
    presenter = OpenCashSessionPresenter(
        view=dialog,
        services=services,
        session=session,
        engine=engine,
    )
    dialog._presenter = presenter
    return dialog
