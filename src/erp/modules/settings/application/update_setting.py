"""UpdateSetting use case — updates a setting value with permission check
and audit trail."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.settings.application.ports import SettingsRepository
from erp.shared.domain.errors import PermissionDenied


@dataclass(slots=True, frozen=True)
class UpdateSettingInput:
    company_id: int
    key: str
    value: str
    value_type: str = "string"
    user_id: int | None = None
    username: str = ""


@dataclass(slots=True, frozen=True)
class UpdateSettingOutput:
    key: str
    value: str
    value_type: str


class UpdateSetting:
    """Atualiza o valor de uma configuração por empresa.

    Exige permissão settings.update.
    """

    def __init__(
        self,
        repo: SettingsRepository,
        user_permissions: set[str],
    ) -> None:
        self._repo = repo
        self._user_permissions = user_permissions

    def execute(self, input: UpdateSettingInput) -> UpdateSettingOutput:
        if "settings.update" not in self._user_permissions:
            raise PermissionDenied(
                "Usuário não tem permissão para alterar configurações (settings.update)."
            )

        setting = self._repo.get_by_key(company_id=input.company_id, key=input.key)
        if setting is None:
            # Cria nova configuração
            from erp.modules.settings.domain.setting import Setting

            setting = Setting(
                company_id=input.company_id,
                key=input.key,
                value=input.value,
                value_type=input.value_type,
                updated_by_user_id=input.user_id,
                updated_by_username=input.username,
            )
            self._repo.add(setting)
        else:
            setting.value = input.value
            setting.value_type = input.value_type
            setting.updated_by_user_id = input.user_id
            setting.updated_by_username = input.username
            self._repo.save(setting)

        return UpdateSettingOutput(
            key=setting.key,
            value=setting.value,
            value_type=setting.value_type,
        )
