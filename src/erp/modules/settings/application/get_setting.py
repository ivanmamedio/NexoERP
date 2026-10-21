"""GetSetting use case — retrieves a typed setting value for a company."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.settings.application.ports import SettingsRepository
from erp.shared.domain.errors import NotFound


@dataclass(slots=True, frozen=True)
class GetSettingInput:
    company_id: int
    key: str


@dataclass(slots=True, frozen=True)
class GetSettingOutput:
    key: str
    value: str
    value_type: str


class GetSetting:
    """Recupera o valor de uma configuração por empresa e chave."""

    def __init__(self, repo: SettingsRepository) -> None:
        self._repo = repo

    def execute(self, input: GetSettingInput) -> GetSettingOutput:
        setting = self._repo.get_by_key(company_id=input.company_id, key=input.key)
        if setting is None:
            raise NotFound(
                f"Configuração '{input.key}' não encontrada para a empresa {input.company_id}."
            )
        return GetSettingOutput(
            key=setting.key,
            value=setting.value,
            value_type=setting.value_type,
        )
