"""CreateUser case of use."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.identity.application.permission_gate import PermissionGate
from erp.modules.identity.application.ports import PasswordHasher, UserRepository
from erp.modules.identity.domain.password_policy import validate_password_policy
from erp.modules.identity.domain.permission import PERMISSION_USER_MANAGE
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User


@dataclass(slots=True, frozen=True)
class CreateUserInput:
    actor_id: int
    employee_name: str
    password: str
    role_name: str
    company_id: int | None = None
    must_change_password: bool = False


@dataclass(slots=True, frozen=True)
class CreateUserOutput:
    user_id: int
    user_number: int
    employee_name: str
    role_name: str


class CreateUser:
    """Cria um novo usuário associado a um papel (requer user.manage).

    Gera user_number sequencial automaticamente (0, 1, 2...).
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        gate: PermissionGate,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._gate = gate

    def execute(
        self,
        data: CreateUserInput,
        role: Role,
    ) -> CreateUserOutput:
        self._gate.require(data.actor_id, PERMISSION_USER_MANAGE.code)

        # Verificar se employee_name já existe (opcional, pode permitir duplicados)
        existing = self._user_repo.list_all()
        if any(u.employee_name == data.employee_name for u in existing):
            raise ValueError(f"Funcionário '{data.employee_name}' já existe")

        validate_password_policy(data.password)
        password_hash = self._password_hasher.hash(data.password)

        # Gerar próximo user_number sequencial
        existing_users = self._user_repo.list_all()
        next_number = max((u.user_number for u in existing_users), default=-1) + 1

        user = User(
            user_number=next_number,
            employee_name=data.employee_name,
            password_hash=self._password_hasher.hash(data.password),
            must_change_password=data.must_change_password,
            company_id=data.company_id,
        )
        self._user_repo.add(user)
        self._user_repo.assign_role(user, role, company_id=data.company_id)
        self._user_repo.save(user)

        return CreateUserOutput(
            user_id=user.id or 0,
            user_number=user.user_number,
            employee_name=user.employee_name,
            role_name=role.name,
        )
