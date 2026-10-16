"""Seed data for identity module: roles, permissions, and initial admin user."""

from __future__ import annotations

from erp.modules.identity.domain.permission import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
)
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.modules.identity.infrastructure.hasher import BcryptHasher


def seed(*, session, password_hasher: BcryptHasher) -> None:
    """Popula papéis, permissões e usuário admin inicial."""
    role_repo = SqlAlchemyRoleRepository(session)
    permission_repo = SqlAlchemyPermissionRepository(session)
    user_repo = SqlAlchemyUserRepository(session)

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

        # Associar permissões ao papel (via tabela de associação)
        # Isso seria feito no repositório concreto; aqui apenas garantimos que existam
        for code in permission_codes:
            perm = permission_repo.get_by_code(code)
            if perm is None:
                perm = Permission(code=code)
                permission_repo.add(perm)

    # 3. Criar usuário admin inicial
    admin = user_repo.get_by_username("admin")
    if admin is None:
        admin_user = User(
            username="admin",
            password_hash=password_hasher.hash("admin123"),
            must_change_password=True,
            is_active=True,
        )
        user_repo.add(admin_user)

    session.commit()
