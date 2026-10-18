"""ChangePasswordPresenter — troca de senha sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.identity.application.services import IdentityServices
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import DomainError


@runtime_checkable
class ChangePasswordView(Protocol):
    """Contrato da tela de troca de senha consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def clear_passwords(self) -> None: ...
    def set_require_current(self, required: bool) -> None: ...
    def accept(self) -> None: ...


class ChangePasswordPresenter:
    """Gerencia troca de senha self-service e troca forçada (primeiro acesso).

    No modo forçado a senha atual não é pedida (o usuário acabou de logar);
    o caso de uso autoriza ``current_password=None`` apenas para o próprio
    usuário ou para administradores com ``user.manage``.
    """

    def __init__(
        self,
        view: ChangePasswordView,
        services: IdentityServices,
        session: CurrentSession,
        *,
        forced: bool = False,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self._forced = forced
        view.set_require_current(not forced)

    def change(
        self,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> bool:
        """Tenta alterar a senha. Retorna True em caso de sucesso."""
        if self._session.user_id is None:
            self._view.show_error("Sessão expirada. Entre novamente.")
            return False

        if not self._forced and not current_password:
            self._view.show_error("Informe a senha atual.")
            return False

        if not new_password or not confirm_password:
            self._view.show_error("Informe a nova senha e a confirmação.")
            return False

        if new_password != confirm_password:
            self._view.show_error("A confirmação não confere com a nova senha.")
            self._view.clear_passwords()
            return False

        try:
            self._services.change_password(
                user_id=self._session.user_id,
                current_password=None if self._forced else current_password,
                new_password=new_password,
                actor_id=self._session.user_id,
            )
        except (ValueError, DomainError) as exc:
            self._view.show_error(str(exc))
            self._view.clear_passwords()
            return False

        self._view.show_info("Senha alterada com sucesso.")
        self._view.accept()
        return True
