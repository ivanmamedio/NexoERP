"""Qt view for company settings."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from erp.modules.companies.infrastructure.models import CompanyModel
from erp.modules.companies.infrastructure.repository import SqlAlchemyCompanyRepository
from erp.modules.identity.infrastructure.models import user_company_role
from erp.modules.settings.application.services import SettingsServices
from erp.modules.settings.presentation.settings_presenter import (
    SettingsPresenter,
)
from erp.shared.application.session import CurrentSession


class SettingsDialog(QDialog):
    """Diálogo de configurações da empresa.

    Implementa estruturalmente o protocolo SettingsView (herdar de um
    Protocol junto de QDialog causa conflito de metaclasse com o PySide6).
    """

    def __init__(
        self,
        presenter: SettingsPresenter | None,
        session: CurrentSession,
        company_name: str,
        engine: Engine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session
        self._engine = engine

        self.setWindowTitle("Configurações da Empresa")
        self.setModal(True)
        self.resize(520, 580)

        self._setup_ui()
        self._load_companies()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Company selector
        company_layout = QFormLayout()
        self._company_combo = QComboBox()
        self._company_combo.setPlaceholderText("Selecione a empresa ativa")
        self._company_combo.currentIndexChanged.connect(self._on_company_changed)
        company_layout.addRow("Empresa ativa:", self._company_combo)
        layout.addLayout(company_layout)

        # Separator
        from PySide6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        form = QFormLayout()

        self._company_name = QLineEdit()
        self._company_name.setPlaceholderText("Nome da empresa")
        form.addRow("Nome da empresa:", self._company_name)

        self._cnpj = QLineEdit()
        self._cnpj.setPlaceholderText("00.000.000/0001-00")
        form.addRow("CNPJ (opcional):", self._cnpj)

        self._address = QLineEdit()
        self._address.setPlaceholderText("Endereço")
        form.addRow("Endereço:", self._address)

        self._receipt_header = QLineEdit()
        self._receipt_header.setPlaceholderText("Mensagem no cabeçalho do cupom")
        form.addRow("Cabeçalho do cupom:", self._receipt_header)

        self._receipt_footer = QLineEdit()
        self._receipt_footer.setPlaceholderText("Mensagem no rodapé do cupom")
        form.addRow("Rodapé do cupom:", self._receipt_footer)

        self._idle_timeout = QSpinBox()
        self._idle_timeout.setRange(1, 480)
        self._idle_timeout.setSuffix(" minutos")
        self._idle_timeout.setValue(30)
        form.addRow("Timeout de sessão ociosa:", self._idle_timeout)

        layout.addLayout(form)

        # Hint
        hint = QLabel("Esses dados aparecem no cabeçalho e rodapé do cupom de venda.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Salvar")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _load_companies(self) -> None:
        """Carrega as empresas disponíveis para o usuário."""
        try:
            with Session(self._engine) as session:
                # Get companies user has access to
                from sqlalchemy import select
                user_id = self._session.user_id
                if user_id is None:
                    return
                
                stmt = (
                    select(CompanyModel.company_id, CompanyModel.name)
                    .join(
                        user_company_role,
                        CompanyModel.company_id == user_company_role.c.company_id,
                    )
                    .where(user_company_role.c.user_id == user_id)
                    .distinct()
                )
                results = session.execute(stmt).all()
                for row in results:
                    self._company_combo.addItem(row.name, row.company_id)
                
                # Select current company
                current_company_id = self._session.company_id
                if current_company_id:
                    idx = self._company_combo.findData(current_company_id)
                    if idx >= 0:
                        self._company_combo.setCurrentIndex(idx)
        except Exception as exc:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar empresas: {exc}")

    def _on_company_changed(self, index: int) -> None:
        """Quando a empresa é alterada, atualiza a sessão."""
        company_id = self._company_combo.currentData()
        if company_id is not None:
            self._session.company_id = company_id
            # Update user's default company
            self._update_user_default_company(company_id)

    def _update_user_default_company(self, company_id: int) -> None:
        """Atualiza a empresa padrão do usuário no banco."""
        try:
            from sqlalchemy.orm import Session as SASession
            from erp.modules.audit.infrastructure.triggers import (
                disable_bypass,
                enable_bypass,
            )
            from erp.modules.identity.infrastructure.models import UserModel
            
            engine = self._engine
            enable_bypass(engine)
            try:
                with SASession(engine) as session:
                    user_model = session.get(UserModel, self._session.user_id)
                    if user_model:
                        user_model.company_id = company_id
                        session.commit()
            finally:
                disable_bypass(engine)
        except Exception:
            pass  # Silencioso - erro será mostrado no save

    def _on_save_clicked(self) -> None:
        if self._presenter is not None:
            self._presenter.save_settings()

    # --- SettingsView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def show_success(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)

    def set_company_name(self, name: str) -> None:
        self._company_name.setText(name)

    def set_cnpj(self, cnpj: str) -> None:
        self._cnpj.setText(cnpj)

    def set_address(self, address: str) -> None:
        self._address.setText(address)

    def set_receipt_header(self, message: str) -> None:
        self._receipt_header.setText(message)

    def set_receipt_footer(self, message: str) -> None:
        self._receipt_footer.setText(message)

    def set_idle_timeout_minutes(self, minutes: int) -> None:
        self._idle_timeout.setValue(minutes)

    def get_company_name(self) -> str:
        return self._company_name.text().strip()

    def get_cnpj(self) -> str:
        return self._cnpj.text().strip()

    def get_address(self) -> str:
        return self._address.text().strip()

    def get_receipt_header(self) -> str:
        return self._receipt_header.text().strip()

    def get_receipt_footer(self) -> str:
        return self._receipt_footer.text().strip()

    def get_idle_timeout_minutes(self) -> int:
        return self._idle_timeout.value()

    def accept(self) -> None:
        super().accept()


def create_settings_dialog(
    services: SettingsServices,
    session: CurrentSession,
    company_name: str,
    engine: Engine,
    parent: QWidget | None = None,
) -> SettingsDialog:
    """Factory para criar o diálogo com presenter injetado."""
    dialog = SettingsDialog(None, session, company_name, engine, parent)
    presenter = SettingsPresenter(
        view=dialog,
        services=services,
        session=session,
        company_name=company_name,
    )
    dialog._presenter = presenter
    return dialog
