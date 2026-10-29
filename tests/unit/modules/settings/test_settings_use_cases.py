"""Unit tests for Settings use cases."""

from __future__ import annotations

import re

import pytest

from erp.modules.settings.application.get_setting import (
    GetSetting,
    GetSettingInput,
)
from erp.modules.settings.application.update_setting import (
    UpdateSetting,
    UpdateSettingInput,
)
from erp.modules.settings.domain.setting import Setting
from erp.shared.domain.errors import NotFound, PermissionDenied


class FakeSettingsRepository:
    def __init__(self) -> None:
        self._settings: dict[tuple[int, str], Setting] = {}

    def add(self, setting: Setting) -> None:
        self._settings[(setting.company_id, setting.key)] = setting

    def save(self, setting: Setting) -> None:
        self._settings[(setting.company_id, setting.key)] = setting

    def get_by_key(self, *, company_id: int, key: str) -> Setting | None:
        return self._settings.get((company_id, key))

    def list_by_company(self, company_id: int) -> list[Setting]:
        return [s for (cid, _), s in self._settings.items() if cid == company_id]

    def delete(self, key: str, company_id: int) -> None:
        self._settings.pop((company_id, key), None)


def _make_setting(company_id: int = 1, key: str = "test_key", value: str = "test_value") -> Setting:
    return Setting(
        company_id=company_id,
        key=key,
        value=value,
        value_type="string",
    )


def test_get_setting_existing() -> None:
    repo = FakeSettingsRepository()
    setting = _make_setting(company_id=1, key="company_name", value="Minha Loja")
    repo.add(setting)

    output = GetSetting(repo).execute(GetSettingInput(company_id=1, key="company_name"))
    assert output.key == "company_name"
    assert output.value == "Minha Loja"
    assert output.value_type == "string"


def test_get_setting_not_found() -> None:
    repo = FakeSettingsRepository()

    with pytest.raises(NotFound, match="não encontrada"):
        GetSetting(repo).execute(GetSettingInput(company_id=1, key="inexistente"))


def test_get_setting_isolation_between_companies() -> None:
    repo = FakeSettingsRepository()
    repo.add(_make_setting(company_id=1, key="company_name", value="Loja A"))
    repo.add(_make_setting(company_id=2, key="company_name", value="Loja B"))

    output_a = GetSetting(repo).execute(GetSettingInput(company_id=1, key="company_name"))
    output_b = GetSetting(repo).execute(GetSettingInput(company_id=2, key="company_name"))
    assert output_a.value == "Loja A"
    assert output_b.value == "Loja B"


def test_update_setting_create_new() -> None:
    repo = FakeSettingsRepository()

    output = UpdateSetting(repo, {"settings.update"}).execute(
        UpdateSettingInput(
            company_id=1,
            key="company_name",
            value="Minha Loja",
            value_type="string",
            user_id=1,
            username="admin",
        )
    )
    assert output.key == "company_name"
    assert output.value == "Minha Loja"

    # Verifica que foi persistido
    setting = repo.get_by_key(company_id=1, key="company_name")
    assert setting is not None
    assert setting.value == "Minha Loja"


def test_update_setting_existing() -> None:
    repo = FakeSettingsRepository()
    repo.add(_make_setting(company_id=1, key="company_name", value="Loja Antiga"))

    output = UpdateSetting(repo, {"settings.update"}).execute(
        UpdateSettingInput(
            company_id=1,
            key="company_name",
            value="Loja Nova",
            value_type="string",
            user_id=1,
            username="admin",
        )
    )
    assert output.value == "Loja Nova"


def test_update_setting_requires_permission() -> None:
    repo = FakeSettingsRepository()

    with pytest.raises(PermissionDenied, match=re.escape("settings.update")):
        UpdateSetting(repo, set()).execute(
            UpdateSettingInput(
                company_id=1,
                key="company_name",
                value="Minha Loja",
                value_type="string",
                user_id=1,
                username="caixa",
            )
        )


def test_update_setting_isolation_between_companies() -> None:
    repo = FakeSettingsRepository()

    UpdateSetting(repo, {"settings.update"}).execute(
        UpdateSettingInput(
            company_id=1,
            key="company_name",
            value="Loja A",
            user_id=1,
            username="admin",
        )
    )
    UpdateSetting(repo, {"settings.update"}).execute(
        UpdateSettingInput(
            company_id=2,
            key="company_name",
            value="Loja B",
            user_id=1,
            username="admin",
        )
    )

    assert repo.get_by_key(company_id=1, key="company_name").value == "Loja A"
    assert repo.get_by_key(company_id=2, key="company_name").value == "Loja B"
