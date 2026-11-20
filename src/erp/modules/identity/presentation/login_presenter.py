"""LoginPresenter — orquestra autenticação sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.identity.application.services import IdentityServices
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import DomainError


@runtime_checkable
class LoginView(Protocol):
    """Contrato da tela de login consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def clear_password(self) -> None: ...
    def accept(self) -> None: ...


class LoginPresenter:
    """Valida entrada, autentica via caso de uso e atualiza a sessão."""

    def __init__(
        self,
        view: LoginView,
        services: IdentityServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self.must_change_password = False

    def login(self, identifier: str, password: str) -> bool:
        """Tenta autenticar. Retorna True em caso de sucesso.

        O ``identifier`` pode ser o número do usuário ou o nome do funcionário.
        """
        if not password:
            self._view.show_error("Informe usuário e senha.")
            return False

        if not identifier or not identifier.strip():
            self._view.show_error("Informe o número ou nome do usuário.")
            return False

        try:
            output = self._services.authenticate(identifier.strip(), password)
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.clear_password()
            return False

        self._session.user_id = output.user_id
        self._session.user_number = output.user_number
        self._session.username = output.employee_name  # compatibilidade
        self._session.company_id = output.company_id
        self.must_change_password = output.must_change_password
        self._view.accept()
        return True

    def logout(self) -> None:
        """Limpa a sessão corrente."""
        self._session.user_id = None
        self._session.user_number = None
        self._session.username = None
        self._session.company_id = None
        self.must_change_password = False
