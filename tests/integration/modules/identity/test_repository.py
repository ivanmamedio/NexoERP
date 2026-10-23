"""Integration tests for identity repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from erp.modules.identity.application.check_permission import (
    CheckPermission,
    CheckPermissionInput,
)
from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.models import (
    PermissionModel,
    RoleModel,
    role_permission,
)
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from erp.modules.identity.infrastructure.seed import create_first_admin, seed
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
        user_number=0,
        employee_name="João",
        password_hash="hash123",
        must_change_password=True,
        is_active=True,
    )
    repo.add(user)

    saved = repo.get_by_user_number(0)
    assert saved is not None
    assert saved.user_number == 0
    assert saved.employee_name == "João"
    assert saved.must_change_password is True

    saved.password_hash = "novo_hash"
    repo.save(saved)

    updated = repo.get_by_user_number(0)
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
    # Segunda chamada deve ser idempotente (não duplica a associação)
    role_repo.add_permission_to_role("Caixa", "product.price.update")
    session.commit()

    # Verificar que a associação existe (recuperar papel e verificar permissão)
    saved_role = role_repo.get_by_name("Caixa")
    assert saved_role is not None

    permission_id = session.execute(
        select(PermissionModel.id).where(PermissionModel.code == "product.price.update")
    ).scalar_one()

    # A associação deve estar no banco (query direta: .all() devolve Rows, não escalares)
    rows = session.execute(
        select(role_permission).where(role_permission.c.role_id == saved_role.id)
    ).all()
    assert len(rows) == 1
    assert rows[0].permission_id == permission_id


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
        employee_name="admin",
        password="senha_segura_123",
    )
    assert admin is not None
    assert admin.employee_name == "admin"
    assert admin.must_change_password is True

    # Segunda tentativa com mesmo employee_name não sobrescreve
    admin2 = create_first_admin(
        session=session,
        password_hasher=hasher,
        employee_name="admin",
        password="outra_senha",
    )
    assert admin2 is None  # Não recria


def test_user_lockout_before_during_after(session: Session) -> None:
    """Bloqueio de login funciona antes, durante e depois do prazo."""
    user = User(
        user_number=999,
        employee_name="teste",
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
    user.locked_until = datetime.now(UTC) - timedelta(minutes=1)
    assert user.is_locked() is False  # Depois do prazo: desbloqueado


def test_locked_until_roundtrip_is_timezone_aware(session: Session) -> None:
    """locked_until lido do banco deve ser aware, senão is_locked() levanta TypeError."""
    repo = SqlAlchemyUserRepository(session)
    user = User(user_number=999, employee_name="bloqueado", password_hash="hash123")
    for _ in range(5):
        user.record_failed_login()
    repo.add(user)
    session.commit()
    session.expire_all()  # força a releitura do banco

    loaded = repo.get_by_user_number(999)
    assert loaded is not None
    assert loaded.locked_until is not None
    assert loaded.locked_until.tzinfo is not None
    assert loaded.is_locked() is True


def test_created_at_is_generated_per_row(session: Session) -> None:
    """created_at deve ser calculado no INSERT, não uma única vez na importação."""
    before = datetime.now(UTC)
    SqlAlchemyRoleRepository(session).add(Role(name="Auditoria"))
    after = datetime.now(UTC)

    model = session.execute(select(RoleModel).where(RoleModel.name == "Auditoria")).scalar_one()
    assert before <= model.created_at <= after


def test_caixa_role_permissions_end_to_end(session: Session) -> None:
    """Regra central da Tarefa 1.1: o Caixa NÃO tem product.price.update
    nem treasury.view (verificado via CheckPermission real sobre o seed)."""
    hasher = BcryptHasher()
    seed(session=session, password_hasher=hasher)

    user_repo = SqlAlchemyUserRepository(session)
    role_repo = SqlAlchemyRoleRepository(session)

    caixa_role = role_repo.get_by_name("Caixa")
    assert caixa_role is not None

    user = User(user_number=999, employee_name="ops_caixa", password_hash="h", is_active=True)
    user_repo.add(user)
    user_repo.assign_role(user, caixa_role)
    session.commit()

    check = CheckPermission(user_repo)
    result = check.execute(
        CheckPermissionInput(user_id=user.id, permission_code="product.price.update")
    )
    assert result.has_permission is False

    result = check.execute(CheckPermissionInput(user_id=user.id, permission_code="treasury.view"))
    assert result.has_permission is False


def test_admin_role_has_all_permissions_end_to_end(session: Session) -> None:
    """Administrador (via create_first_admin) tem todas as permissões do seed."""
    hasher = BcryptHasher()
    seed(session=session, password_hasher=hasher)

    admin = create_first_admin(
        session=session,
        password_hasher=hasher,
        employee_name="admin",
        password="senha_segura_123",
    )
    assert admin is not None
    session.commit()

    user_repo = SqlAlchemyUserRepository(session)
    check = CheckPermission(user_repo)

    for code in ("product.price.update", "treasury.view", "backup.manage"):
        result = check.execute(CheckPermissionInput(user_id=admin.id, permission_code=code))
        assert result.has_permission is True, f"admin deveria ter {code}"
