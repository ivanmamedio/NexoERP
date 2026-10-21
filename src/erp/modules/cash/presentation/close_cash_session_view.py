"""Qt view for closing cash session."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine

from erp.modules.cash.application.services import CashServices
from erp.modules.cash.presentation.close_cash_session_presenter import (
    CloseCashSessionPresenter,
    CloseCashSessionView,
)
from erp.shared.application.session import CurrentSession


class CloseCashSessionDialog(QDialog, CloseCashSessionView):
    """Diálogo para fechar sessão de caixa."""

    def __init__(
        self,
        presenter: CloseCashSessionPresenter | None,
        session: CurrentSession,
        session_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session_id = session_id

        self.setWindowTitle("Fechar Sessão de Caixa")
        self.setModal(True)
        self.resize(450, 350)

        self._setup_ui()
        if self._presenter is not None:
            self._presenter.load_session()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._info_label = QLabel(f"Fechando sessão: {self._session_id}")
        layout.addWidget(self._info_label)

        self._expected_label = QLabel("Esperado: R$ 0,00")
        self._expected_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._expected_label)

        form = QFormLayout()

        self._counted_spin = QSpinBox()
        self._counted_spin.setRange(0, 99999999)
        self._counted_spin.setSuffix(" centavos")
        self._counted_spin.setGroupSeparatorShown(True)
        form.addRow("Valor contado (centavos):", self._counted_spin)

        self._blind_checkbox = QCheckBox("Fechamento cego (não mostrar valores)")
        self._blind_checkbox.toggled.connect(self._on_blind_toggled)
        layout.addWidget(self._blind_checkbox)

        self._pix_spin = QSpinBox()
        self._pix_spin.setRange(0, 99999999)
        self._pix_spin.setSuffix(" centavos")
        self._pix_spin.setGroupSeparatorShown(True)
        form.addRow("Total PIX (centavos):", self._pix_spin)

        self._card_spin = QSpinBox()
        self._card_spin.setRange(0, 99999999)
        self._card_spin.setSuffix(" centavos")
        self._card_spin.setGroupSeparatorShown(True)
        form.addRow("Total Cartão (centavos):", self._card_spin)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._close_btn = QPushButton("Fechar Sessão")
        self._close_btn.setDefault(True)
        self._close_btn.clicked.connect(self._on_close_clicked)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

    def _on_blind_toggled(self, checked: bool) -> None:
        self._counted_spin.setEnabled(not checked)
        if checked:
            self._counted_spin.setValue(0)

    def _on_close_clicked(self) -> None:
        if self._presenter is not None and self._presenter.close_session():
            self.accept()

    # --- CloseCashSessionView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def show_success(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)

    def set_session_info(self, session_id: int, expected_cash: int) -> None:
        self._info_label.setText(f"Fechando sessão: {session_id}")
        self._expected_label.setText(f"Esperado em dinheiro: R$ {expected_cash / 100:.2f}")

    def get_counted_amount_cents(self) -> int:
        return self._counted_spin.value()

    def is_blind_close(self) -> bool:
        return self._blind_checkbox.isChecked()

    def get_pix_cents(self) -> int:
        return self._pix_spin.value()

    def get_card_cents(self) -> int:
        return self._card_spin.value()

    def accept(self) -> None:
        super().accept()


def create_close_cash_session_dialog(
    services: CashServices,
    session: CurrentSession,
    session_id: int,
    engine: Engine,
    parent: QWidget | None = None,
) -> CloseCashSessionDialog:
    """Factory para criar o diálogo com presenter injetado."""
    dialog = CloseCashSessionDialog(None, session, session_id, parent)
    presenter = CloseCashSessionPresenter(
        view=dialog,
        services=services,
        session=session,
        session_id=session_id,
        engine=engine,
    )
    dialog._presenter = presenter
    return dialog
