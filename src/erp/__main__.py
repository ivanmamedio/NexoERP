"""Entry point: python -m erp.

Fluxo de identidade:
  1. Bootstrap (banco, migrations, seed).
  2. Splash screen com logo.
  3. Tela de login (modal).
  4. Se must_change_password=True -> tela de troca de senha (forçada).
  4. MainWindow com menus filtrados por permissão e guarda de sessão ociosa.
  5. Ao expirar a sessão ociosa, volta para o login.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from sqlalchemy.engine import Engine

from erp.app.identity_services import SqlIdentityServices
from erp.bootstrap import bootstrap
from erp.config.settings import get_session_timeout_minutes
from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.application.session import CurrentSession
from erp.ui.resource_paths import resource_path
from erp.ui.splash import NexoERPSplashScreen, show_splash_screen

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

    from erp.app.main_window import MainWindow
    from erp.modules.cash.application.services import CashServices
    from erp.modules.reports.application.service import ReportService
    from erp.modules.sales.application.ports import SupervisorAuthPort
    from erp.modules.sales.application.services import SalesServices
    from erp.modules.settings.application.services import SettingsServices

_logger = logging.getLogger(__name__)


class _AppContextHolder:
    engine: Engine | None = None
    cash_services: CashServices | None = None
    sales_services: SalesServices | None = None
    report_service: ReportService | None = None
    settings_services: SettingsServices | None = None
    supervisor_auth: SupervisorAuthPort | None = None


class _App:
    """Orquestra janelas de login, troca de senha e janela principal."""

    def __init__(self, app: QApplication, services: IdentityServices) -> None:
        self._app = app
        self._services = services
        self._session = CurrentSession()
        self._main_window: MainWindow | None = None

    def run(self, splash: NexoERPSplashScreen | None = None) -> int:
        while True:
            self._session = CurrentSession()
            if not self._has_any_user():
                first_use_done = self._show_first_use()
                if not first_use_done:
                    # Usuário cancelou o primeiro uso; não pode prosseguir sem admin.
                    return 0
                continue

            logged_in = self._show_login()
            if not logged_in:
                return 0

            if self._session.user_id is None:
                continue

            if self._session.username and self._must_change_password():
                changed = self._show_change_password(forced=True)
                if not changed:
                    continue

            self._open_main_window()
            # Fecha splash quando janela principal abrir
            if splash is not None and self._main_window is not None:
                splash.finish(self._main_window)
            while self._main_window is not None and self._main_window.isVisible():
                self._app.processEvents()
        # Unreachable, but needed for type checker
        return 0

    def _has_any_user(self) -> bool:
        """Verifica se já existe pelo menos um usuário cadastrado."""
        engine = _AppContextHolder.engine
        if engine is None:
            return False
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            user_repo = SqlAlchemyUserRepository(session)
            return len(user_repo.list_all()) > 0

    def _show_first_use(self) -> bool:
        """Mostra a tela de primeiro uso para criar o primeiro administrador."""
        from erp.modules.identity.presentation.first_use_presenter import (
            FirstUsePresenter,
        )
        from erp.modules.identity.presentation.first_use_view import FirstUseDialog

        engine = _AppContextHolder.engine
        if engine is None:
            return False
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            hasher = BcryptHasher()
            user_repo = SqlAlchemyUserRepository(session)
            role_repo = SqlAlchemyRoleRepository(session)
            dialog = FirstUseDialog()
            presenter = FirstUsePresenter(
                view=dialog,
                user_repo=user_repo,
                password_hasher=hasher,
                session=self._session,
                role_repository=role_repo,
            )
            dialog.set_presenter(presenter)
            result = dialog.exec()
            session.commit()
            return result == QDialog.DialogCode.Accepted

    def _show_login(self) -> bool:
        from erp.modules.identity.presentation.login_presenter import LoginPresenter
        from erp.modules.identity.presentation.login_view import LoginDialog

        dialog = LoginDialog()
        presenter = LoginPresenter(dialog, self._services, self._session)
        dialog.set_presenter(presenter)
        dialog.exec()
        return self._session.is_authenticated()

    def _must_change_password(self) -> bool:
        from erp.modules.identity.infrastructure.unit_of_work import (
            SqlAlchemyIdentityUnitOfWork,
        )

        engine = _AppContextHolder.engine
        if engine is None:
            return False
        with SqlAlchemyIdentityUnitOfWork(engine) as uow:
            assert uow.users is not None
            user = uow.users.get_by_id(self._session.user_id or 0)
            if user is None:
                return False
            return bool(user.must_change_password)

    def _show_change_password(self, *, forced: bool) -> bool:
        from erp.modules.identity.presentation.change_password_presenter import (
            ChangePasswordPresenter,
        )
        from erp.modules.identity.presentation.change_password_view import (
            ChangePasswordDialog,
        )

        dialog = ChangePasswordDialog()
        presenter = ChangePasswordPresenter(dialog, self._services, self._session, forced=forced)
        dialog.set_presenter(presenter)
        dialog.exec()
        return not self._session.username or not self._must_change_password()

    def _open_main_window(self) -> None:
        from erp.app.main_window import MainWindow

        engine = _AppContextHolder.engine
        if engine is None:
            return
        timeout_minutes = get_session_timeout_minutes()
        self._main_window = MainWindow(
            services=self._services,
            session=self._session,
            idle_timeout_seconds=timeout_minutes * 60,
        )
        self._main_window.change_password_requested.connect(self._on_change_password_requested)
        self._main_window.users_requested.connect(self._on_users_requested)
        self._main_window.companies_requested.connect(self._on_companies_requested)
        self._main_window.catalog_requested.connect(self._on_catalog_requested)
        self._main_window.pos_requested.connect(self._on_pos_requested)
        self._main_window.cash_requested.connect(self._on_cash_requested)
        self._main_window.treasury_requested.connect(self._on_treasury_requested)
        self._main_window.reports_requested.connect(self._on_reports_requested)
        self._main_window.settings_requested.connect(self._on_settings_requested)
        self._main_window.audit_requested.connect(self._on_audit_requested)
        self._main_window.session_expired.connect(self._on_session_expired)
        self._main_window.start_session_guard()
        self._main_window.show()

    def _on_change_password_requested(self) -> None:
        self._show_change_password(forced=False)

    def _on_users_requested(self) -> None:
        from PySide6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self._main_window)
        layout = QVBoxLayout(dialog)
        from erp.modules.identity.presentation.users_presenter import UsersPresenter
        from erp.modules.identity.presentation.users_view import UsersWidget

        widget = UsersWidget(dialog)
        layout.addWidget(widget)
        dialog.setWindowTitle("Gerenciar Usuários")
        dialog.resize(700, 500)
        presenter = UsersPresenter(widget, self._services, self._session)
        widget.set_presenter(presenter)
        presenter.load()
        dialog.exec()

    def _on_companies_requested(self) -> None:
        from PySide6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
        )
        from sqlalchemy.orm import Session

        from erp.modules.companies.infrastructure.repository import (
            SqlAlchemyCompanyRepository,
        )

        engine = _AppContextHolder.engine
        if engine is None:
            return

        dialog = QDialog(self._main_window)
        dialog.setWindowTitle("Empresas")
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Razão social", "Nome fantasia", "CNPJ", "Ativa"])
        table.horizontalHeader().setSectionResizeMode(table.horizontalHeader().ResizeMode.Stretch)
        layout.addWidget(table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Nova Empresa")
        btn_close = QPushButton("Fechar")
        btn_layout.addStretch()
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        def _load_companies() -> None:
            with Session(engine) as session:
                repo = SqlAlchemyCompanyRepository(session)
                companies = repo.list_all()
                table.setRowCount(len(companies))
                for row, c in enumerate(companies):
                    table.setItem(row, 0, QTableWidgetItem(c.name or ""))
                    table.setItem(row, 1, QTableWidgetItem(c.trade_name or ""))
                    table.setItem(row, 2, QTableWidgetItem(c.tax_id or ""))
                    table.setItem(row, 3, QTableWidgetItem("Sim" if c.active else "Não"))

        def _on_add() -> None:
            from erp.modules.companies.application.create_company import (
                CreateCompany,
                CreateCompanyInput,
            )

            create_dialog = QDialog(dialog)
            create_dialog.setWindowTitle("Nova Empresa")
            create_dialog.resize(400, 300)
            create_layout = QVBoxLayout(create_dialog)

            from PySide6.QtWidgets import QDialogButtonBox, QFormLayout, QLineEdit

            form = QFormLayout()
            name = QLineEdit()
            name.setPlaceholderText("Razão social")
            trade = QLineEdit()
            trade.setPlaceholderText("Nome fantasia")
            tax = QLineEdit()
            tax.setPlaceholderText("CNPJ")
            addr = QLineEdit()
            addr.setPlaceholderText("Endereço")
            phone = QLineEdit()
            phone.setPlaceholderText("Telefone")
            email = QLineEdit()
            email.setPlaceholderText("E-mail")
            form.addRow("Razão social:", name)
            form.addRow("Nome fantasia:", trade)
            form.addRow("CNPJ:", tax)
            form.addRow("Endereço:", addr)
            form.addRow("Telefone:", phone)
            form.addRow("E-mail:", email)
            create_layout.addLayout(form)

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Salvar")
            buttons.accepted.connect(create_dialog.accept)
            buttons.rejected.connect(create_dialog.reject)
            create_layout.addWidget(buttons)

            if create_dialog.exec():
                with Session(engine) as session:
                    repo = SqlAlchemyCompanyRepository(session)
                    use_case = CreateCompany(repo)
                    use_case.execute(
                        CreateCompanyInput(
                            name=name.text().strip(),
                            trade_name=trade.text().strip(),
                            tax_id=tax.text().strip(),
                            address=addr.text().strip(),
                            phone=phone.text().strip(),
                            email=email.text().strip(),
                        )
                    )
                    session.commit()
                _load_companies()

        btn_add.clicked.connect(_on_add)
        btn_close.clicked.connect(dialog.reject)
        _load_companies()
        dialog.exec()

    def _on_catalog_requested(self) -> None:
        from PySide6.QtWidgets import (
            QDialog,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
        )
        from sqlalchemy.orm import Session

        from erp.modules.catalog.domain.product import Product
        from erp.modules.catalog.infrastructure.repository import (
            SqlAlchemyProductRepository,
        )

        engine = _AppContextHolder.engine
        if engine is None:
            return

        dialog = QDialog(self._main_window)
        dialog.setWindowTitle("Catálogo / Produtos")
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(
            ["SKU", "Nome", "Unidade", "Preço", "Custo", "Estoque", "Estoque Baixo"]
        )
        table.horizontalHeader().setSectionResizeMode(table.horizontalHeader().ResizeMode.Stretch)
        layout.addWidget(table)

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.reject)
        layout.addWidget(btn_close)

        def _load_products() -> None:
            with Session(engine) as session:
                repo = SqlAlchemyProductRepository(session)
                products: list[Product] = repo.list_all()
                table.setRowCount(len(products))
                for row, p in enumerate(products):
                    table.setItem(row, 0, QTableWidgetItem(p.sku or ""))
                    table.setItem(row, 1, QTableWidgetItem(p.name or ""))
                    table.setItem(row, 2, QTableWidgetItem(p.unit or ""))
                    table.setItem(row, 3, QTableWidgetItem(f"{p.price_cents / 100:.2f}"))
                    table.setItem(row, 4, QTableWidgetItem(f"{p.cost_cents / 100:.2f}"))
                    table.setItem(row, 5, QTableWidgetItem(f"{p.stock_qty / 1000:.3f}"))
                    table.setItem(row, 6, QTableWidgetItem("Sim" if p.is_low_stock() else "Não"))

        _load_products()
        dialog.exec()

    def _on_pos_requested(self) -> None:
        from erp.modules.sales.presentation.pos_view import create_pos_dialog

        engine = _AppContextHolder.engine
        sales_services = _AppContextHolder.sales_services
        supervisor_auth = _AppContextHolder.supervisor_auth
        if engine is None or sales_services is None or supervisor_auth is None:
            return

        dialog = create_pos_dialog(
            sales_services=sales_services,
            supervisor_auth=supervisor_auth,
            session=self._session,
            session_id=None,
            parent=self._main_window,
        )
        dialog.exec()

    def _on_cash_requested(self) -> None:
        from PySide6.QtWidgets import (
            QDialog,
            QPushButton,
            QVBoxLayout,
        )

        from erp.modules.cash.presentation.open_cash_session_view import (
            create_open_cash_session_dialog,
        )

        engine = _AppContextHolder.engine
        cash_services = _AppContextHolder.cash_services
        if engine is None or cash_services is None:
            return

        dialog = QDialog(self._main_window)
        dialog.setWindowTitle("Caixa / Sessões")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)

        btn_open = QPushButton("Abrir Sessão de Caixa")
        btn_close = QPushButton("Sair")

        for btn in (btn_open, btn_close):
            layout.addWidget(btn)

        def _open_session() -> None:
            dlg = create_open_cash_session_dialog(
                services=cash_services,
                session=self._session,
                engine=engine,
                parent=dialog,
            )
            if dlg.exec():
                pass

        btn_open.clicked.connect(_open_session)
        btn_close.clicked.connect(dialog.reject)
        dialog.exec()

    def _on_treasury_requested(self) -> None:
        from erp.modules.treasury.application.services import TreasuryServices
        from erp.modules.treasury.presentation.treasury_dashboard import (
            create_treasury_dashboard_dialog,
        )

        engine = _AppContextHolder.engine
        if engine is None:
            return

        treasury_services = TreasuryServices(engine=engine)
        dialog = create_treasury_dashboard_dialog(
            services=treasury_services,
            session=self._session,
            engine=engine,
            parent=self._main_window,
        )
        dialog.exec()

    def _on_reports_requested(self) -> None:
        from erp.modules.reports.presentation.dialog import create_report_dialog

        report_service = _AppContextHolder.report_service
        if report_service is None:
            return

        company_id = self._session.company_id
        if company_id is None:
            return

        dialog = create_report_dialog(
            report_service=report_service,
            company_id=company_id,
            parent=self._main_window,
        )
        dialog.exec()

    def _on_settings_requested(self) -> None:
        from erp.modules.settings.presentation.settings_view import (
            create_settings_dialog,
        )

        settings_services = _AppContextHolder.settings_services
        engine = _AppContextHolder.engine
        if settings_services is None or engine is None:
            return

        company_id = self._session.company_id
        company_name = ""
        if company_id is not None:
            from sqlalchemy.orm import Session

            from erp.modules.companies.infrastructure.repository import (
                SqlAlchemyCompanyRepository,
            )

            with Session(engine) as session:
                repo = SqlAlchemyCompanyRepository(session)
                company = repo.get_by_id(company_id)
                if company is not None:
                    company_name = company.name

        dialog = create_settings_dialog(
            services=settings_services,
            session=self._session,
            company_name=company_name,
            engine=engine,
            parent=self._main_window,
        )
        dialog.exec()

    def _on_audit_requested(self) -> None:
        from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout
        from sqlalchemy.orm import Session

        from erp.modules.audit.infrastructure.repository import SqlAlchemyAuditRepository
        from erp.modules.audit.presentation.audit_view import AuditLogWidget

        engine = _AppContextHolder.engine
        if engine is None:
            return

        dialog = QDialog(self._main_window)
        dialog.setWindowTitle("Log de Auditoria")
        dialog.resize(900, 600)
        layout = QVBoxLayout(dialog)

        widget = AuditLogWidget(dialog)
        layout.addWidget(widget)

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.reject)
        layout.addWidget(btn_close)

        with Session(engine) as session:
            repo = SqlAlchemyAuditRepository(session)
            entries = repo.list_all()
            widget.set_entries(entries)

        dialog.exec()

    def _on_session_expired(self) -> None:
        _logger.info("Sessão expirada por ociosidade")
        if self._main_window is not None:
            self._main_window.close()
            self._main_window = None


def main() -> int:
    try:
        ctx = bootstrap()
        _AppContextHolder.engine = ctx.engine
        _AppContextHolder.cash_services = ctx.cash_services
        _AppContextHolder.sales_services = ctx.sales_services
        _AppContextHolder.report_service = ctx.report_service
        _AppContextHolder.settings_services = ctx.settings_services
        _AppContextHolder.supervisor_auth = ctx.supervisor_auth
        _logger.info("Bootstrap successful. DB path: %s", ctx.db_path)
    except Exception:
        _logger.exception("Bootstrap failed")
        return 1

    if "CODESPACES" in os.environ or not os.environ.get("DISPLAY"):
        _logger.info("Running in headless environment. Skipping UI launch.")
        _logger.info("Run 'uv run pytest' to validate the infrastructure.")
        return 0

    from PySide6 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    # Splash screen - usa helper de recursos
    logo_path = resource_path("erp", "ui", "resources", "logo.png")
    splash = show_splash_screen(logo_path, duration_ms=0)  # 0 = não auto-fechar
    splash.showMessage(
        "Carregando módulos...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.white,
    )

    services: IdentityServices = SqlIdentityServices(ctx.engine)
    runner = _App(app, services)

    exit_code = runner.run(splash=splash)

    # Backup no fechamento do app
    try:
        if ctx.backup_service is not None:
            ctx.backup_service.create_backup("app_shutdown", str(ctx.db_path), "app_shutdown")
    except Exception:
        _logger.exception("Falha no backup de fechamento do app")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
