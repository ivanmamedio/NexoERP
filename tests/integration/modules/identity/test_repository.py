"""Integration tests for identity repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.seed import create_first_admin, seed
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.shared.infrastructure.database import Base


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_user_crud(session: Session) -> None:
    repo = SqlAlchemyUserRepository(session)

    user = User(
        username="joao",
        password_hash="hash123",
        must_change_password=True,
        is_active=True,
    )
    repo.add(user)

    saved = repo.get_by_username("joao")
    assert saved is not None
    assert saved.username == "joao"
    assert saved.must_change_password is True

    saved.password_hash = "novo_hash"
    repo.save(saved)

    updated = repo.get_by_username("joao")
    assert updated is not None
    assert updated.password_hash == "novo_hash"


def test_role_crud(session: Session) -> None:
    repo = SqlAlchemyRoleRepository(session)

    role = Role(name="Caixa", description="Papel de caixa", is_active=True)
    repo.add(role)

    saved = repo.get_by_name("Caixa")
    assert saved is not None
    assert saved.name == "Caixa"
    assert saved.is_active is True


def test_permission_crud(session: Session) -> None:
    repo = SqlAlchemyPermissionRepository(session)

    perm = Permission(code="product.price.update")
    repo.add(perm)

    saved = repo.get_by_code("product.price.update")
    assert saved is not None
    assert saved.code == "product.price.update"

    all_perms = repo.get_all()
    assert len(all_perms) == 1


def test_bcrypt_hasher_roundtrip() -> None:
    hasher = BcryptHasher()
    hashed = hasher.hash("senha123")
    assert hashed != "senha123"
    assert hasher.verify("senha123", hashed) is True
    assert hasher.verify("senha_errada", hashed) is False


def test_role_permission_persistence(session: Session) -> None:
    """Permissões de papel são persistidas na tabela role_permissions."""
    role_repo = SqlAlchemyRoleRepository(session)
    perm_repo = SqlAlchemyPermissionRepository(session)

    role = Role(name="Caixa", description="Papel de caixa", is_active=True)
    role_repo.add(role)

    perm = Permission(code="product.price.update")
    perm_repo.add(perm)

    role_repo.add_permission_to_role("Caixa", "product.price.update")
    session.commit()

    # Verificar que a associação existe (recuperar papel e verificar permissão)
    saved_role = role_repo.get_by_name("Caixa")
    assert saved_role is not None

    # A associação deve estar no banco (verificar via query direta)
    from erp.modules.identity.infrastructure.models import role_permission
    from sqlalchemy import select

    result = session.execute(
        select(role_permission).where(
            role_permission.c.role_id == saved_role.id,
        )
    ).scalars().all()
    assert len(result) == 1
    assert result[0].permission_id is not None


def test_seed_idempotent(session: Session) -> None:
    """Seed pode ser executado múltiplas vezes sem duplicar dados."""
    hasher = BcryptHasher()
    seed(session=session, password_hasher=hasher)
    seed(session=session, password_hasher=hasher)  # segunda vez

    perm_repo = SqlAlchemyPermissionRepository(session)
    perms = perm_repo.get_all()
    assert len(perms) == len({p.code for p in perms})  # sem duplicatas


def test_create_first_admin(session: Session) -> None:
    """Primeiro administrador é criado com credenciais explícitas."""
    hasher = BcryptHasher()

    # Primeira criação
    admin = create_first_admin(
        session=session,
        password_hasher=hasher,
        username="admin",
        password="senha_segura_123",
    )
    assert admin is not None
    assert admin.username == "admin"
    assert admin.must_change_password is True

    # Segunda tentativa com mesmo username não sobrescreve
    admin2 = create_first_admin(
        session=session,
        password_hasher=hasher,
        username="admin",
        password="outra_senha",
    )
    assert admin2 is None  # Não recria


def test_user_lockout_before_during_after(session: Session) -> None:
    """Bloqueio de login funciona antes, durante e depois do prazo."""
    user = User(
        username="teste",
        password_hash="hash123",
        must_change_password=False,
        is_active=True,
    )

    # Antes: não bloqueado
    assert user.is_locked() is False

    # Simular 5 tentativas falhas
    for _ in range(5):
        user.record_failed_login()

    # Durante: bloqueado (locked_until definido no futuro)
    assert user.failed_login_attempts == 5
    assert user.is_locked() is True
    assert user.locked_until is not None

    # Simular expiração do bloqueio (definir locked_until no passado)
    from datetime import datetime, timezone, timedelta
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert user.is_locked() is False  # Depois do prazo: desbloqueado
