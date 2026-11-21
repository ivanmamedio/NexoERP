"""FirstUsePresenter — cria o primeiro administrador e a empresa sem dependência de Qt."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from PySide6.QtWidgets import QApplication

from erp.modules.companies.application.create_company import CreateCompany, CreateCompanyInput
from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.identity.application.create_first_user import (
    CreateFirstUser,
    CreateFirstUserInput,
)
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.password_policy import validate_password_policy
from erp.modules.identity.domain.role import Role
from erp.modules.identity.infrastructure.repository import SqlAlchemyRoleRepository
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import DomainError
from erp.shared.infrastructure.password_hasher import SyncBcryptHasher


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
    def get_company_name(self) -> str: ...
    def get_company_tax_id(self) -> str: ...


class FirstUsePresenter:
    """Cria o primeiro usuário administrador do sistema e a empresa associada.

    Não exige permissão user.manage (não há usuário autenticado ainda).
    """

    def __init__(
        self,
        view: FirstUseView,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        session: CurrentSession,
        role_repository: SqlAlchemyRoleRepository,
        company_repo: CompanyRepository,
    ) -> None:
        self._view = view
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._session = session
        self._role_repository = role_repository
        self._company_repo = company_repo

    def create_first_user(
        self,
        username: str,
        password: str,
        confirm_password: str,
    ) -> bool:
        """Cria o primeiro admin e a empresa. Retorna True em caso de sucesso."""
        # Validações do admin
        if not username or not password or not confirm_password:
            self._view.show_error("Informe nome, senha e confirmação do administrador.")
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

        # Validações da empresa
        company_name = self._view.get_company_name().strip()
        if not company_name:
            self._view.show_error("Informe o nome da empresa.")
            self._view.clear_passwords()
            return False

        company_tax_id = self._view.get_company_tax_id().strip()

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

        # Show confirmation dialog
        confirm_msg = (
            f"Confirma a criação do primeiro administrador e da empresa?\n\n"
            f"<b>Administrador:</b>\n"
            f"Nome: {username}\n"
            f"Perfil: Administrador\n"
            f"ID (Número do Usuário): 0\n\n"
            f"<b>Empresa:</b>\n"
            f"Nome: {company_name}\n"
            f"CNPJ: {company_tax_id if company_tax_id else '(será gerado placeholder)'}\n\n"
            f"IMPORTANTE: O login será feito com o NÚMERO DO USUÁRIO (0)."
        )

        self._view.show_confirmation(
            confirm_msg,
            on_confirm=lambda: self._do_create_first_user(username, password, role, company_name, company_tax_id),
            on_cancel=lambda: self._view.clear_passwords(),
        )
        return True

    def _do_create_first_user(
        self,
        username: str,
        password: str,
        role: Role,
        company_name: str,
        company_tax_id: str,
    ) -> None:
        """Executa a criação do admin + empresa com hash síncrono."""
        self._view.set_loading(True)
        self._view.show_info("Criando administrador e empresa... Aguarde.")
        QApplication.processEvents()

        try:
            # 1. Hash síncrono da senha
            password_hash = self._password_hasher.hash(password)

            # 2. Cria o usuário administrador
            use_case = CreateFirstUser(self._user_repo, self._password_hasher)
            output = use_case.execute(
                CreateFirstUserInput(
                    employee_name=username,
                    password_hash=password_hash,
                    role_name=role.name,
                ),
                role=role,
            )

            # 3. Prepara dados da empresa
            tax_id = company_tax_id if company_tax_id else self._generate_placeholder_cnpj()

            # 4. Cria a empresa
            company_use_case = CreateCompany(self._company_repo)
            company_output = company_use_case.execute(
                CreateCompanyInput(
                    name=company_name,
                    trade_name=company_name,
                    tax_id=tax_id,
                    address="",
                    phone="",
                    email="",
                    active=True,
                )
            )
            company = company_output.company

            # 5. Associa o usuário à empresa com role de Administrador
            # Usa o método do repositório que já lida com a tabela user_company_role
            assert company.company_id is not None, "Empresa deve ter ID após criação"
            self._user_repo.assign_user_to_company(
                user_id=output.user_id,
                company_id=company.company_id,
                role_name="Administrador",
            )

            # 6. Define a empresa como padrão do usuário (default company)
            # Atualiza o campo company_id no UserModel
            from erp.modules.identity.infrastructure.models import UserModel

            user_repo_impl = self._user_repo
            if hasattr(user_repo_impl, '_session') and user_repo_impl._session:
                session = user_repo_impl._session
                user_model = session.get(UserModel, output.user_id)
                if user_model:
                    user_model.company_id = company.company_id
                    session.flush()

        except (ValueError, DomainError) as exc:
            self._view.set_loading(False)
            self._view.show_error(str(exc))
            self._view.clear_passwords()
            return
        except Exception as exc:
            self._view.set_loading(False)
            self._view.show_error(f"Erro inesperado: {exc}")
            self._view.clear_passwords()
            return

        # Define a sessão para o usuário recém-criado
        self._session.user_id = output.user_id
        self._session.username = output.employee_name
        self._session.company_id = company.company_id  # Empresa já selecionada!

        # Mostra sucesso com número do usuário e empresa
        self._view.show_info(
            f"Administrador e empresa criados com sucesso!\n\n"
            f"<b>Administrador:</b>\n"
            f"Nome: {output.employee_name}\n"
            f"Número do Usuário (ID): {output.user_number}\n\n"
            f"<b>Empresa:</b>\n"
            f"Nome: {company.name}\n"
            f"CNPJ: {company.tax_id}\n\n"
            f"IMPORTANTE: Guarde o número do usuário ({output.user_number}) para fazer login!\n"
            f"O login é feito com o NÚMERO DO USUÁRIO, não com o nome."
        )
        self._view.set_loading(False)
        self._view.accept()

    def _generate_placeholder_cnpj(self) -> str:
        """Gera um CNPJ placeholder único para primeiro uso."""
        import time
        # Formato: 00.000.000/0001-XX onde XX é baseado no timestamp
        suffix = int(time.time() * 1000) % 100
        return f"00.000.000/0001-{suffix:02d}"
