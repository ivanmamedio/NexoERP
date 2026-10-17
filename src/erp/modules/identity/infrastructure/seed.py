"""Seed data for identity module: roles, permissions, and initial admin user."""

from __future__ import annotations

import os

from sqlalchemy.orm import Session

from erp.modules.identity.domain.permission import ALL_PERMISSIONS, ROLE_PERMISSIONS, Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)


def seed(*, session: Session, password_hasher: BcryptHasher) -> None:
    """Popula papéis e permissões do sistema.

    Não cria usuário administrador automaticamente. Use
    create_first_admin() para isso, fornecendo credenciais explícitas.
    """
    role_repo = SqlAlchemyRoleRepository(session)
    permission_repo = SqlAlchemyPermissionRepository(session)

    # 1. Criar permissões
    for perm in ALL_PERMISSIONS:
        existing = permission_repo.get_by_code(perm.code)
        if existing is None:
            permission_repo.add(perm)

    # 2. Criar papéis e associar permissões
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = role_repo.get_by_name(role_name)
        if role is None:
            role = Role(name=role_name, description=f"Papel {role_name}", is_active=True)
            role_repo.add(role)

        # Associar permissões ao papel (via tabela de associação role_permissions)
        for code in permission_codes:
            existing = permission_repo.get_by_code(code)
            if existing is None:
                new_perm = Permission(code=code)
                permission_repo.add(new_perm)
            role_repo.add_permission_to_role(role_name, code)

    session.commit()


def create_first_admin(
    *,
    session: Session,
    password_hasher: BcryptHasher,
    username: str,
    password: str,
) -> User | None:
    """Cria o primeiro usuário administrador, se ainda não existir.

    Não recria nem redefine a senha se o usuário já existe.
    Não grava senha em texto puro em nenhum log ou arquivo.
    """
    user_repo = SqlAlchemyUserRepository(session)

    existing = user_repo.get_by_username(username)
    if existing is not None:
        return None  # Não sobrescreve usuário existente

    admin_user = User(
        username=username,
        password_hash=password_hasher.hash(password),
        must_change_password=True,
        is_active=True,
    )
    user_repo.add(admin_user)
    session.commit()
    return admin_user


def get_admin_seed_password() -> str | None:
    """Lê a senha de seed do admin de variável de ambiente, se configurada.

    Não é usada automaticamente. Apenas disponível para scripts de
    inicialização que queiram definir a senha via variável de ambiente.
    Retorna None se não configurada.
    """
    return os.environ.get("NEXOERP_ADMIN_PASSWORD")
