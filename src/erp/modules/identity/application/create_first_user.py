"""CreateFirstUser case of use — cria o primeiro administrador do sistema.

Usado apenas na tela de Primeiro Uso, quando ainda não existe nenhum
usuário cadastrado. Não exige permissão user.manage (não há usuário
logado ainda).
"""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.password_policy import validate_password_policy
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User


@dataclass(slots=True, frozen=True)
class CreateFirstUserInput:
    employee_name: str
    password: str
    role_name: str = "Administrador"


@dataclass(slots=True, frozen=True)
class CreateFirstUserOutput:
    user_id: int
    user_number: int
    employee_name: str
    role_name: str
    is_first_admin: bool = False


class CreateFirstUser:
    """Cria o primeiro usuário administrador do sistema.

    Não exige permissão user.manage (não há usuário autenticado).
    Define must_change_password=True para forçar a troca na próxima sessão.
    O user_number do primeiro admin é sempre 0.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    def execute(
        self,
        data: CreateFirstUserInput,
        role: Role,
    ) -> CreateFirstUserOutput:
        if self._user_repo.list_all() is not None and len(self._user_repo.list_all()) > 0:
            raise ValueError("Já existe pelo menos um usuário cadastrado.")

        validate_password_policy(data.password)
        password_hash = self._password_hasher.hash(data.password)

        user = User(
            user_number=0,  # Primeiro admin sempre tem user_number = 0
            employee_name=data.employee_name,
            password_hash=password_hash,
            must_change_password=True,
            is_active=True,
        )
        self._user_repo.add(user)
        self._user_repo.assign_role(user, role)
        self._user_repo.save(user)

        is_first_admin = user.user_number == 0
        return CreateFirstUserOutput(
            user_id=user.id or 0,
            user_number=user.user_number,
            employee_name=user.employee_name,
            role_name=role.name,
            is_first_admin=is_first_admin,
        )
