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

        sistema = menubar.addMenu("&Sistema")
        action_change_password = sistema.addAction("Alterar &senha...")
        action_change_password.triggered.connect(self.change_password_requested)
        sistema.addSeparator()
        action_quit = sistema.addAction("&Sair")
        action_quit.triggered.connect(self.close)

        # Menu Usuários: apenas para quem tem user.manage
        if self._has_permission("user.manage"):
            usuarios = menubar.addMenu("&Usuários")
            action_manage = usuarios.addAction("&Gerenciar usuários...")
            action_manage.triggered.connect(self.users_requested)

        # Placeholder para os módulos das próximas fases: mostra apenas os
        # menus cuja permissão o usuário possui (nada de botão órfão).
        self._build_future_module_menus(menubar)

    def _build_future_module_menus(self, menubar: object) -> None:
        """Pré-configura menus de módulos futuros já filtrando por permissão.

        Eles só aparecem quando o módulo correspondente existir; por ora,
        apenas registra quais permissões cada módulo exigirá.
        """
        # Mantido vazio de propósito: os módulos (vendas, estoque, caixa...)
        # serão adicionados nas fases seguintes com seus próprios presenters.

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
