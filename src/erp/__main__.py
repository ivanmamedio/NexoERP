"""Entry point: python -m erp.

Fluxo de identidade:
  1. Bootstrap (banco, migrations, seed).
  2. Splash screen com logo.
  3. Tela de login (modal).
  4. Se must_change_password=True -> tela de troca de senha (forçada).
  5. Seleção de empresa (se usuário tem acesso a múltiplas).
  6. MainWindow com menus filtrados por permissão e guarda de sessão ociosa.
  7. Ao expirar a sessão ociosa, volta para o login.
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
from erp.modules.catalog.application.services import SqlAlchemyCatalogServices
from erp.modules.identity.application.services import IdentityServices
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.application.events import EventBus
from erp.shared.application.session import CurrentSession
from erp.shared.ui.exception_handler import install_global_exception_handler
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
    catalog_services: SqlAlchemyCatalogServices | None = None
    event_bus: EventBus | None = None


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

            # Seleção de empresa após login/senha
            company_selected = self._show_company_selection()
            if not company_selected:
                # Usuário cancelou seleção de empresa -> volta para login
                self._session = CurrentSession()
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

    def _show_company_selection(self) -> bool:
        """Mostra diálogo de seleção de empresa se usuário tem acesso a múltiplas.

        Retorna True se empresa foi selecionada, False se usuário cancelou.
        """
        engine = _AppContextHolder.engine
        if engine is None:
            return False

        from sqlalchemy import select
        from sqlalchemy.orm import Session

        from erp.modules.companies.infrastructure.models import CompanyModel
        from erp.modules.identity.infrastructure.models import user_company_role
        from erp.modules.identity.presentation.select_company_presenter import (
            SelectCompanyPresenter,
        )
        from erp.modules.identity.presentation.select_company_view import (
            SelectCompanyDialog,
        )

        dialog = SelectCompanyDialog(parent=self._main_window)
        presenter = SelectCompanyPresenter(view=dialog, session=self._session)
        dialog.set_presenter(presenter)

        # Load companies for current user
        user_id = self._session.user_id
        if user_id is None:
            return False

        try:
            with Session(engine) as session:
                stmt = (
                    select(CompanyModel.id, CompanyModel.name)
                    .join(
                        user_company_role,
                        CompanyModel.company_id == user_company_role.c.company_id,
                    )
                    .where(user_company_role.c.user_id == user_id)
                    .distinct()
                )
                results = session.execute(stmt).all()
                companies = [(row.id, row.name) for row in results]
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(dialog, "Erro", f"Erro ao carregar empresas: {exc}")
            return False

        if not companies:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                dialog,
                "Aviso",
                "Você não tem acesso a nenhuma empresa. Contate o administrador.",
            )
            return False

        if len(companies) == 1:
            # Apenas uma empresa - seleciona automaticamente
            self._session.company_id = companies[0][0]
            # Atualiza company_id no usuário (default company) - precisa bypass do audit trigger
            from sqlalchemy.orm import Session as SASession

            from erp.modules.audit.infrastructure.triggers import (
                disable_bypass,
                enable_bypass,
            )
            from erp.modules.identity.infrastructure.models import UserModel

            enable_bypass(engine)
            try:
                with SASession(engine) as session:
                    user_model = session.get(UserModel, self._session.user_id)
                    if user_model:
                        user_model.company_id = companies[0][0]
                        session.commit()
            finally:
                disable_bypass(engine)
            return True

        # Múltiplas empresas - mostra lista para seleção
        dialog.render_companies(companies)

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            company_id = dialog.get_selected_company_id()
            if company_id is not None:
                self._session.company_id = company_id
                # Atualiza company_id no usuário (default company) - precisa bypass do audit trigger
                from sqlalchemy.orm import Session as SASession

                from erp.modules.audit.infrastructure.triggers import (
                    disable_bypass,
                    enable_bypass,
                )
                from erp.modules.identity.infrastructure.models import UserModel

                enable_bypass(engine)
                try:
                    with SASession(engine) as session:
                        user_model = session.get(UserModel, self._session.user_id)
                        if user_model:
                            user_model.company_id = company_id
                            session.commit()
                finally:
                    disable_bypass(engine)
                return True
        return False

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
            engine=engine,
        )
        self._main_window.change_password_requested.connect(self._on_change_password_requested)
        self._main_window.users_requested.connect(self._on_users_requested)
        self._main_window.companies_requested.connect(self._on_companies_requested)
        self._main_window.catalog_requested.connect(self._on_catalog_requested)
        self._main_window.price_requested.connect(self._on_price_requested)
        self._main_window.pos_requested.connect(self._on_pos_requested)
        self._main_window.cash_requested.connect(self._on_cash_requested)
        self._main_window.treasury_requested.connect(self._on_treasury_requested)
        self._main_window.reports_requested.connect(self._on_reports_requested)
        self._main_window.graphical_reports_requested.connect(self._on_graphical_reports_requested)
        self._main_window.settings_requested.connect(self._on_settings_requested)
        self._main_window.audit_requested.connect(self._on_audit_requested)
        self._main_window.credit_notebook_requested.connect(self._on_credit_notebook_requested)
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
        from sqlalchemy.orm import Session

        from erp.modules.companies.application.services import CompaniesServices
        from erp.modules.companies.presentation.list_companies_view import (
            create_companies_list_dialog,
        )
        from erp.modules.identity.infrastructure.repository import SqlAlchemyUserRepository

        engine = _AppContextHolder.engine
        if engine is None:
            return

        with Session(engine) as session:
            user_repo = SqlAlchemyUserRepository(session)

        companies_services = CompaniesServices(
            engine=engine,
            user_company_assigner=user_repo,
        )
        dialog = create_companies_list_dialog(
            services=companies_services,
            session=self._session,
            parent=self._main_window,
        )
        dialog.exec()

    def _on_catalog_requested(self) -> None:
        from erp.modules.catalog.presentation.catalog_dialog import create_catalog_dialog

        engine = _AppContextHolder.engine
        catalog_services = _AppContextHolder.catalog_services
        if engine is None or catalog_services is None:
            return

        dialog = create_catalog_dialog(
            services=catalog_services,
            session=self._session,
            engine=engine,
            parent=self._main_window,
        )
        dialog.exec()

    def _on_price_requested(self) -> None:
        from erp.modules.catalog.presentation.price_dialog import create_price_dialog

        engine = _AppContextHolder.engine
        catalog_services = _AppContextHolder.catalog_services
        if engine is None or catalog_services is None:
            return

        dialog = create_price_dialog(
            services=catalog_services,
            session=self._session,
            engine=engine,
            parent=self._main_window,
        )
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
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        from erp.modules.cash.presentation.open_cash_session_view import (
            create_open_cash_session_dialog,
        )

        engine = _AppContextHolder.engine
        cash_services = _AppContextHolder.cash_services
        sales_services = _AppContextHolder.sales_services
        supervisor_auth = _AppContextHolder.supervisor_auth
        if (
            engine is None
            or cash_services is None
            or sales_services is None
            or supervisor_auth is None
        ):
            return

        dialog = QDialog(self._main_window)
        dialog.setWindowTitle("Caixa / Sessões")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)

        btn_open = QPushButton("Abrir Sessão de Caixa")
        btn_open.setMinimumHeight(50)
        btn_open.setStyleSheet("font-size: 14px; font-weight: bold;")

        btn_pdv = QPushButton("Abrir PDV (Venda)")
        btn_pdv.setMinimumHeight(50)
        btn_pdv.setStyleSheet(
            "font-size: 14px; font-weight: bold; background-color: #27ae60; color: white;"
        )
        btn_pdv.setEnabled(False)  # Habilitado apenas após abrir caixa

        btn_close = QPushButton("Sair")

        for btn in (btn_open, btn_pdv, btn_close):
            layout.addWidget(btn)

        def _open_session() -> None:
            dlg = create_open_cash_session_dialog(
                services=cash_services,
                session=self._session,
                engine=engine,
                parent=dialog,
            )
            if dlg.exec():
                # Caixa aberto com sucesso - habilitar PDV
                btn_pdv.setEnabled(True)
                QMessageBox.information(
                    dialog, "Sucesso", "Caixa aberto! O PDV está disponível para vendas."
                )

        def _open_pdv() -> None:
            # Obter a sessão de caixa aberta
            from erp.modules.cash.infrastructure.unit_of_work import SqlAlchemyCashUnitOfWork
            from erp.modules.sales.presentation.pos_view import create_pos_dialog

            # Buscar sessão aberta para o usuário/empresa atual
            try:
                with SqlAlchemyCashUnitOfWork(engine) as uow:
                    assert uow.sessions is not None
                    sessions = uow.sessions.list_by_company(company_id=self._session.company_id)
                    open_sessions = [
                        s
                        for s in sessions
                        if s.status == "open" and s.opened_by_user_id == self._session.user_id
                    ]

                    if not open_sessions:
                        QMessageBox.warning(
                            dialog,
                            "Aviso",
                            "Nenhuma sessão de caixa aberta encontrada para este usuário.",
                        )
                        return

                    # Usar a sessão mais recente
                    session_id = open_sessions[0].id
            except Exception:
                _logger.exception("Erro ao buscar sessão de caixa aberta.")
                QMessageBox.warning(dialog, "Erro", "Erro ao buscar sessão de caixa.")
                return

            pdv_dialog = create_pos_dialog(
                sales_services=sales_services,
                supervisor_auth=supervisor_auth,
                session=self._session,
                session_id=session_id,
                parent=self._main_window,
            )
            pdv_dialog.exec()

        btn_open.clicked.connect(_open_session)
        btn_pdv.clicked.connect(_open_pdv)
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

    def _on_graphical_reports_requested(self) -> None:
        from erp.modules.reports.presentation.graphical_reports_dialog import (
            create_graphical_reports_dialog,
        )

        report_service = _AppContextHolder.report_service
        if report_service is None:
            return

        company_id = self._session.company_id
        if company_id is None:
            return

        # Create session factory for the dialog
        from sqlalchemy.orm import Session

        def session_factory() -> Session:
            return Session(_AppContextHolder.engine)

        dialog = create_graphical_reports_dialog(
            report_service=report_service,
            company_id=company_id,
            session_factory=session_factory,
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

    def _on_credit_notebook_requested(self) -> None:
        from erp.modules.credit_notebook.application.services import CreditNotebookServices
        from erp.modules.credit_notebook.presentation.credit_notebook_view import (
            create_credit_notebook_dialog,
        )

        engine = _AppContextHolder.engine
        if engine is None:
            return

        services = CreditNotebookServices(engine=engine)
        dialog = create_credit_notebook_dialog(
            services=services,
            session=self._session,
            engine=engine,
            parent=self._main_window,
        )
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
        _AppContextHolder.catalog_services = ctx.catalog_services
        _AppContextHolder.event_bus = ctx.event_bus
        _logger.info("Bootstrap successful. DB path: %s", ctx.db_path)
    except Exception:
        _logger.exception("Bootstrap failed")
        return 1

    if "CODESPACES" in os.environ or (os.name != "nt" and not os.environ.get("DISPLAY")):
        _logger.info("Running in headless environment. Skipping UI launch.")
        _logger.info("Run 'uv run pytest' to validate the infrastructure.")
        return 0

    from PySide6 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    # Instala handler global de exceções
    install_global_exception_handler(app, ctx.engine)

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

    exit_code = 0
    try:
        exit_code = runner.run(splash=splash)
    finally:
        # Garante que o splash seja fechado mesmo se houver erro
        if splash is not None:
            try:
                splash.close()
            except Exception:
                _logger.exception("Erro ao fechar splash screen")

    # Backup no fechamento do app
    try:
        if ctx.backup_service is not None:
            ctx.backup_service.create_backup("app_shutdown", str(ctx.db_path), "app_shutdown")
    except Exception:
        _logger.exception("Falha no backup de fechamento do app")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
