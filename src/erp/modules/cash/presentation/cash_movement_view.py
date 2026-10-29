"""Qt view for cash movements (sangria/suprimento)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.cash.application.services import CashServices
from erp.modules.cash.presentation.cash_movement_presenter import (
    CashMovementPresenter,
    CashMovementView,
    MovementType,
)
from erp.shared.application.session import CurrentSession


class CashMovementDialog(QDialog, CashMovementView):
    """Diálogo para sangria ou suprimento."""

    def __init__(
        self,
        presenter: CashMovementPresenter | None,
        session: CurrentSession,
        movement_type: str,
        session_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._movement_type = movement_type
        self._session_id = session_id

        title = (
            "Sangria (Retirada)"
            if movement_type == MovementType.SANGRIA
            else "Suprimento (Depósito)"
        )
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 250)

        self._setup_ui()
        if self._presenter is not None:
            self._presenter.load_session()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._info_label = QLabel(f"Sessão: {self._session_id}")
        layout.addWidget(self._info_label)

        form = QFormLayout()

        self._amount_spin = QSpinBox()
        self._amount_spin.setRange(1, 99999999)
        self._amount_spin.setSuffix(" centavos")
        self._amount_spin.setGroupSeparatorShown(True)
        form.addRow("Valor (centavos):", self._amount_spin)

        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Descrição opcional")
        self._description_edit.setMaximumHeight(80)
        form.addRow("Descrição:", self._description_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        action_text = (
            "Registrar Sangria"
            if self._movement_type == MovementType.SANGRIA
            else "Registrar Suprimento"
        )
        self._action_btn = QPushButton(action_text)
        self._action_btn.setDefault(True)
        self._action_btn.clicked.connect(self._on_action_clicked)
        btn_layout.addWidget(self._action_btn)

        layout.addLayout(btn_layout)

    def _on_action_clicked(self) -> None:
        if self._presenter is not None and self._presenter.execute_movement():
            self.accept()

    # --- CashMovementView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def show_success(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)

    def set_session_info(self, session_id: int, status: str) -> None:
        self._info_label.setText(f"Sessão: {session_id} | Status: {status}")

    def get_amount_cents(self) -> int:
        return self._amount_spin.value()

    def get_description(self) -> str:
        return self._description_edit.toPlainText().strip()

    def accept(self) -> None:
        super().accept()


def create_cash_movement_dialog(
    services: CashServices,
    session: CurrentSession,
    movement_type: str,
    session_id: int,
    engine: Engine,
    parent: QWidget | None = None,
) -> CashMovementDialog:
    """Factory para criar o diálogo com presenter injetado."""
    dialog = CashMovementDialog(None, session, movement_type, session_id, parent)
    presenter = CashMovementPresenter(
        view=dialog,
        services=services,
        session=session,
        movement_type=movement_type,
        session_id=session_id,
        engine=engine,
    )
    dialog._presenter = presenter
    return dialog
