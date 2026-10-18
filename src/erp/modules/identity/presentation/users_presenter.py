"""UsersPresenter — gestão de usuários e papéis sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.identity.application.list_roles import RoleListItem
from erp.modules.identity.application.list_users import UserListItem
from erp.modules.identity.application.services import IdentityServices
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import DomainError


@runtime_checkable
class UsersView(Protocol):
    """Contrato da tela de gestão de usuários consumido pelo presenter."""

    def render_users(self, users: list[UserListItem]) -> None: ...
    def render_roles(self, roles: list[RoleListItem]) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def clear_user_form(self) -> None: ...
    def selected_user_id(self) -> int | None: ...


class UsersPresenter:
    """Carrega usuários/papéis e executa as operações de gestão.

    Todas as chamadas passam pelos casos de uso — a permissão ``user.manage``
    é verificada lá, não apenas escondendo botões.
    """

    def __init__(
        self,
        view: UsersView,
        services: IdentityServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def load(self) -> None:
        """Recarrega a lista de usuários e de papéis."""
        actor_id = self._require_actor()
        if actor_id is None:
            return
        try:
            users = self._services.list_users(actor_id=actor_id)
            roles = self._services.list_roles(actor_id=actor_id)
        except (ValueError, DomainError) as exc:
            self._view.show_error(str(exc))
            return
        self._view.render_users(list(users.users))
        self._view.render_roles(list(roles.roles))

    def create_user(self, username: str, password: str, role_name: str) -> None:
        """Cria um usuário com troca de senha obrigatória no primeiro acesso."""
        actor_id = self._require_actor()
        if actor_id is None:
            return

        username = username.strip()
        if not username:
            self._view.show_error("Informe o nome de usuário.")
            return
        if not password:
            self._view.show_error("Informe a senha inicial.")
            return
        if not role_name:
            self._view.show_error("Selecione um papel.")
            return

        try:
            output = self._services.create_user(
                username=username,
                password=password,
                role_name=role_name,
                actor_id=actor_id,
                must_change_password=True,
            )
        except (ValueError, DomainError) as exc:
            self._view.show_error(str(exc))
            return

        self._view.show_info(f"Usuário '{output.username}' criado com papel '{output.role_name}'.")
        self._view.clear_user_form()
        self.load()

    def assign_role(self, role_name: str) -> None:
        """Atribui o papel selecionado ao usuário selecionado na tabela."""
        actor_id = self._require_actor()
        if actor_id is None:
            return

        user_id = self._view.selected_user_id()
        if user_id is None:
            self._view.show_error("Selecione um usuário na tabela.")
            return
        if not role_name:
            self._view.show_error("Selecione um papel.")
            return

        try:
            output = self._services.assign_role(
                user_id=user_id, role_name=role_name, actor_id=actor_id
            )
        except (ValueError, DomainError) as exc:
            self._view.show_error(str(exc))
            return

        self._view.show_info(f"Papel '{output.role_name}' atribuído com sucesso.")
        self.load()

    def set_active(self, is_active: bool) -> None:
        """Ativa ou desativa o usuário selecionado na tabela."""
        actor_id = self._require_actor()
        if actor_id is None:
            return

        user_id = self._view.selected_user_id()
        if user_id is None:
            self._view.show_error("Selecione um usuário na tabela.")
            return

        try:
            self._services.set_user_active(
                user_id=user_id, is_active=is_active, actor_id=actor_id
            )
        except (ValueError, DomainError) as exc:
            self._view.show_error(str(exc))
            return

        action = "ativado" if is_active else "desativado"
        self._view.show_info(f"Usuário {action} com sucesso.")
        self.load()

    def _require_actor(self) -> int | None:
        if self._session.user_id is None:
            self._view.show_error("Sessão expirada. Entre novamente.")
            return None
        return self._session.user_id
