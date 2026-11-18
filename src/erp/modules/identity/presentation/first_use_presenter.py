"""FirstUsePresenter — cria o primeiro administrador sem dependência de Qt."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from erp.modules.identity.application.create_first_user import (
    CreateFirstUser,
    CreateFirstUserInput,
)
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.password_policy import validate_password_policy
from erp.modules.identity.infrastructure.repository import SqlAlchemyRoleRepository
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import DomainError
from erp.shared.infrastructure.password_hasher import AsyncBcryptHasher


@runtime_checkable
class FirstUseView(Protocol):
    """Contrato da tela de primeiro uso consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def clear_passwords(self) -> None: ...
    def accept(self) -> None: ...
    def set_loading(self, loading: bool) -> None: ...
    def show_confirmation(
        self,
        message: str,
        on_confirm: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None: ...


class FirstUsePresenter:
    """Cria o primeiro usuário administrador do sistema.

    Não exige permissão user.manage (não há usuário autenticado ainda).
    """

    def __init__(
        self,
        view: FirstUseView,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        session: CurrentSession,
        role_repository: SqlAlchemyRoleRepository,
    ) -> None:
        self._view = view
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._session = session
        self._role_repository = role_repository
        self._async_hasher = AsyncBcryptHasher()

    def create_first_user(
        self,
        username: str,
        password: str,
        confirm_password: str,
    ) -> bool:
        """Cria o primeiro admin. Retorna True em caso de sucesso."""
        if not username or not password or not confirm_password:
            self._view.show_error("Informe usuário, senha e confirmação.")
            self._view.clear_passwords()
            return False

        if password != confirm_password:
            self._view.show_error("A confirmação não confere com a senha.")
            self._view.clear_passwords()
            return False

        try:
            validate_password_policy(password)
        except ValueError as exc:
            self._view.show_error(str(exc))
            self._view.clear_passwords()
            return False

        # Verifica se já existe usuário (segurança em profundidade)
        existing = self._user_repo.get_by_user_number(0)  # Admin sempre tem user_number 0
        if existing is not None:
            self._view.show_error("Usuário administrador já existe.")
            self._view.clear_passwords()
            return False

        all_users = self._user_repo.list_all()
        if all_users is not None and len(all_users) > 0:
            self._view.show_error("Já existe pelo menos um usuário cadastrado.")
            self._view.clear_passwords()
            return False

        role = self._role_repository.get_by_name("Administrador")
        if role is None:
            self._view.show_error("Papel 'Administrador' não encontrado.")
            return False

        # Show confirmation dialog with user ID preview (0 for first admin)
        confirm_msg = (
            f"Confirma a criação do primeiro administrador?\n\n"
            f"Usuário: {username}\n"
            f"Perfil: Administrador\n"
            f"ID (Número do Usuário): 0\n\n"
            f"IMPORTANTE: O login será feito com o NÚMERO DO USUÁRIO (0).\n"
            f"Essa informação será mostrada novamente após a criação."
        )

        self._view.show_confirmation(
            confirm_msg,
            on_confirm=lambda: self._do_create_first_user(username, password, role),
            on_cancel=lambda: self._view.clear_passwords(),
        )
        return True

    def _do_create_first_user(self, username: str, password: str, role) -> None:
        """Executa a criação com hash assíncrono."""
        self._view.set_loading(True)
        self._view.show_info("Criando usuário... Isso pode levar alguns segundos.")

        def _on_hash_success(password_hash: str) -> None:
            try:
                use_case = CreateFirstUser(self._user_repo, self._password_hasher)
                output = use_case.execute(
                    CreateFirstUserInput(
                        employee_name=username,
                        password_hash=password_hash,
                        role_name=role.name,
                    ),
                    role=role,
                )
            except (ValueError, DomainError) as exc:
                self._view.set_loading(False)
                self._view.show_error(str(exc))
                self._view.clear_passwords()
                return

            # Define a sessão para o usuário recém-criado
            self._session.user_id = output.user_id
            self._session.username = output.employee_name
            self._session.company_id = None  # Será selecionado após o login

            # Mostra o número gerado (0 para o primeiro admin)
            if output.is_first_admin:
                self._view.show_info(
                    f"Primeiro administrador criado com sucesso!\n\n"
                    f"Seu número de usuário (ID) é: {output.user_number}\n\n"
                    f"IMPORTANTE: Guarde este número para fazer login!\n"
                    f"O login é feito com o NÚMERO DO USUÁRIO, não com o nome."
                )
            else:
                self._view.show_info(
                    f"Usuário '{output.employee_name}' criado com sucesso!\n\n"
                    f"Seu número de usuário (ID) é: {output.user_number}\n\n"
                    f"Guarde este número para fazer login."
                )
            self._view.set_loading(False)
            self._view.accept()

        def _on_hash_error(error_msg: str) -> None:
            self._view.set_loading(False)
            self._view.show_error(f"Erro ao processar senha: {error_msg}")
            self._view.clear_passwords()

        # Hash assíncrono
        self._async_hasher.hash_async(
            password,
            on_success=_on_hash_success,
            on_error=_on_hash_error,
        )
