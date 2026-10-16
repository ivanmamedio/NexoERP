"""Integration tests for identity repositories using SQLite in-memory."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, clear_mappers
from typing import Generator

from erp.modules.identity.domain.permission import Permission
from erp.modules.identity.domain.role import Role
from erp.modules.identity.domain.user import User
from erp.modules.identity.infrastructure.hasher import BcryptHasher
from erp.modules.identity.infrastructure.models import Base
from erp.modules.identity.infrastructure.repository import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    clear_mappers()


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
