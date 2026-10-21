"""FirstUsePresenter — cria o primeiro administrador sem dependência de Qt."""

from __future__ import annotations

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


@runtime_checkable
class FirstUseView(Protocol):
    """Contrato da tela de primeiro uso consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def clear_passwords(self) -> None: ...
    def accept(self) -> None: ...


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
        existing = self._user_repo.get_by_username(username)
        if existing is not None:
            self._view.show_error(f"Usuário '{username}' já existe.")
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

        try:
            use_case = CreateFirstUser(self._user_repo, self._password_hasher)
            use_case.execute(
                CreateFirstUserInput(
                    username=username,
                    password=password,
                    role_name=role.name,
                ),
                role=role,
            )
        except (ValueError, DomainError) as exc:
            self._view.show_error(str(exc))
            self._view.clear_passwords()
            return False

        # Define a sessão para o usuário recém-criado
        self._session.user_id = 1  # Será corrigido após o login real
        self._session.username = username
        self._session.company_id = None  # Será selecionado após o login

        self._view.show_info("Primeiro administrador criado com sucesso.")
        self._view.accept()
        return True
