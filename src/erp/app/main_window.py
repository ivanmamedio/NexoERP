"""Janela principal do ERP: menus filtrados por permissão + sessão ociosa."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStatusBar,
)

from erp.modules.identity.application.services import IdentityServices
from erp.shared.application.session import CurrentSession
from erp.shared.ui.idle_timer import IdleSessionTimer


class _ActivityWatcher(QObject):
    """Filtra eventos globais de mouse/teclado e reinicia o timer de ociosidade."""

    def __init__(self, on_activity: Callable[[], None]) -> None:
        super().__init__()
        self._on_activity = on_activity

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.Wheel,
        ):
            self._on_activity()
        return super().eventFilter(watched, event)


class MainWindow(QMainWindow):
    """Janela principal. Menus são exibidos conforme as permissões do usuário.

    Esconder menus é apenas conforto — a verificação real de permissão
    acontece nos casos de uso (PermissionGate).
    """

    #: Emitido pelo menu "Alterar senha...".
    change_password_requested = Signal()
    #: Emitido pelo menu "Gerenciar usuários...".
    users_requested = Signal()
    #: Emitido pelo menu "Empresas".
    companies_requested = Signal()
    #: Emitido pelo menu "Catálogo / Produtos".
    catalog_requested = Signal()
    #: Emitido pelo menu "PDV / Vendas".
    pos_requested = Signal()
    #: Emitido pelo menu "Caixa".
    cash_requested = Signal()
    #: Emitido pelo menu "Tesouraria / Fluxo de Caixa".
    treasury_requested = Signal()
    #: Emitido pelo menu "Relatórios".
    reports_requested = Signal()
    #: Emitido pelo menu "Configurações".
    settings_requested = Signal()
    #: Emitido pelo menu "Auditoria".
    audit_requested = Signal()
    #: Emitido quando a sessão expira por ociosidade (deve voltar ao login).
    session_expired = Signal()

    def __init__(
        self,
        *,
        services: IdentityServices,
        session: CurrentSession,
        idle_timeout_seconds: float,
        parent: QMainWindow | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session
        self.setWindowTitle("NexoERP")
        self.resize(1000, 700)

        self._placeholder = QLabel("Selecione um módulo no menu.", self)
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self._placeholder)

        status = QStatusBar(self)
        username = session.username or "—"
        status.showMessage(f"Usuário: {username}")
        self.setStatusBar(status)

        self._idle_timer = IdleSessionTimer(idle_timeout_seconds)
        self._poll_interval_ms = 5_000
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self._poll_interval_ms)
        self._poll_timer.timeout.connect(self._check_idle)
        self._watcher = _ActivityWatcher(self._idle_timer.register_activity)

        self._build_menus()

    # --- lifecycle ----------------------------------------------------------

    def start_session_guard(self) -> None:
        """Instala o watcher de atividade e inicia a contagem de ociosidade."""
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self._watcher)
        self._idle_timer.register_activity()
        self._poll_timer.start()

    def stop_session_guard(self) -> None:
        """Remove o watcher e para a contagem (ao voltar para o login)."""
        self._poll_timer.stop()
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self._watcher)

    def closeEvent(self, event: object) -> None:
        self.stop_session_guard()
        super().closeEvent(event)  # type: ignore[arg-type]

    # --- menus --------------------------------------------------------------

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        # Sistema
        sistema = menubar.addMenu("&Sistema")
        action_change_password = sistema.addAction("Alterar &senha...")
        action_change_password.triggered.connect(self.change_password_requested)
        sistema.addSeparator()
        action_quit = sistema.addAction("&Sair")
        action_quit.triggered.connect(self.close)

        # Cadastros
        if self._has_permission("company.view") or self._has_permission("company.manage"):
            cadastros = menubar.addMenu("&Cadastros")
            if self._has_permission("company.view"):
                action_companies = cadastros.addAction("&Empresas...")
                action_companies.triggered.connect(self.companies_requested)
            if self._has_permission("product.view") or self._has_permission("product.manage"):
                action_catalog = cadastros.addAction("&Produtos / Catálogo...")
                action_catalog.triggered.connect(self.catalog_requested)

        # Vendas / PDV
        if self._has_permission("sale.view") or self._has_permission("sale.create"):
            vendas = menubar.addMenu("&Vendas")
            action_pos = vendas.addAction("&PDV / Ponto de Venda...")
            action_pos.triggered.connect(self.pos_requested)

        # Caixa
        if self._has_permission("cash.view") or self._has_permission("cash.open_close"):
            caixa = menubar.addMenu("Cai&xa")
            action_cash = caixa.addAction("&Caixa / Sessões...")
            action_cash.triggered.connect(self.cash_requested)

        # Tesouraria
        if self._has_permission("treasury.view"):
            tesouraria = menubar.addMenu("&Tesouraria")
            action_treasury = tesouraria.addAction("&Fluxo de Caixa...")
            action_treasury.triggered.connect(self.treasury_requested)

        # Relatórios
        if self._has_permission("reports.view"):
            relatorios = menubar.addMenu("&Relatórios")
            action_reports = relatorios.addAction("&Gerar Relatório...")
            action_reports.triggered.connect(self.reports_requested)

        # Configurações
        if self._has_permission("settings.update"):
            configuracoes = menubar.addMenu("Con&figurações")
            action_settings = configuracoes.addAction("&Configurações...")
            action_settings.triggered.connect(self.settings_requested)

        # Auditoria
        if self._has_permission("audit.view"):
            auditoria = menubar.addMenu("&Auditoria")
            action_audit = auditoria.addAction("&Log de Auditoria...")
            action_audit.triggered.connect(self.audit_requested)

        # Usuários (apenas para quem tem user.manage)
        if self._has_permission("user.manage"):
            usuarios = menubar.addMenu("&Usuários")
            action_manage = usuarios.addAction("&Gerenciar usuários...")
            action_manage.triggered.connect(self.users_requested)

    def _has_permission(self, code: str) -> bool:
        if self._session.user_id is None:
            return False
        return self._services.check_permission(user_id=self._session.user_id, permission_code=code)

    # --- idle ---------------------------------------------------------------

    def _check_idle(self) -> None:
        if self._idle_timer.is_expired():
            self._poll_timer.stop()
            self.stop_session_guard()
            self.session_expired.emit()
