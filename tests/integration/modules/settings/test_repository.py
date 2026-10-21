"""Integration tests for settings repositories using SQLite in-memory."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.settings.domain.setting import Setting
from erp.modules.settings.infrastructure.models import (
    Base,
)
from erp.modules.settings.infrastructure.repository import (
    SqlAlchemySettingsRepository,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_setting_crud(session: Session) -> None:
    repo = SqlAlchemySettingsRepository(session)

    setting = Setting(
        company_id=1,
        key="company_name",
        value="Minha Loja",
        value_type="string",
    )
    repo.add(setting)
    assert setting.id is not None

    saved = repo.get_by_key(company_id=1, key="company_name")
    assert saved is not None
    assert saved.value == "Minha Loja"

    setting.value = "Loja Atualizada"
    repo.save(setting)

    saved = repo.get_by_key(company_id=1, key="company_name")
    assert saved is not None
    assert saved.value == "Loja Atualizada"

    settings = repo.list_by_company(company_id=1)
    assert len(settings) == 1


def test_setting_isolation_between_companies(session: Session) -> None:
    repo = SqlAlchemySettingsRepository(session)

    repo.add(Setting(company_id=1, key="company_name", value="Loja A"))
    repo.add(Setting(company_id=2, key="company_name", value="Loja B"))

    settings_1 = repo.list_by_company(company_id=1)
    settings_2 = repo.list_by_company(company_id=2)

    assert len(settings_1) == 1
    assert settings_1[0].value == "Loja A"
    assert len(settings_2) == 1
    assert settings_2[0].value == "Loja B"

    # Empresa 1 não deve ver a config da empresa 2
    found = repo.get_by_key(company_id=1, key="company_name")
    assert found is not None
    assert found.value == "Loja A"

    found = repo.get_by_key(company_id=2, key="company_name")
    assert found is not None
    assert found.value == "Loja B"
