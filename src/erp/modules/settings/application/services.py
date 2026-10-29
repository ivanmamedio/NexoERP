"""Application services facade for Settings."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.settings.application.get_setting import (
    GetSetting,
    GetSettingInput,
    GetSettingOutput,
)
from erp.modules.settings.application.update_setting import (
    UpdateSetting,
    UpdateSettingInput,
    UpdateSettingOutput,
)
from erp.modules.settings.infrastructure.unit_of_work import (
    SqlAlchemySettingsUnitOfWork,
)


class SettingsServices:
    """Facade de casos de uso de configurações sobre SQLAlchemy (1 transação por operação)."""

    def __init__(
        self,
        engine: Engine,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._engine = engine
        self._user_permissions = user_permissions or set()

    def get_setting(self, *, company_id: int, key: str) -> GetSettingOutput:
        with SqlAlchemySettingsUnitOfWork(self._engine) as uow:
            assert uow.settings is not None
            result = GetSetting(uow.settings).execute(
                GetSettingInput(company_id=company_id, key=key)
            )
            uow.commit()
            return result

    def update_setting(
        self,
        *,
        company_id: int,
        key: str,
        value: str,
        value_type: str = "string",
        user_id: int | None = None,
        username: str = "",
    ) -> UpdateSettingOutput:
        with SqlAlchemySettingsUnitOfWork(self._engine) as uow:
            assert uow.settings is not None
            result = UpdateSetting(uow.settings, self._user_permissions).execute(
                UpdateSettingInput(
                    company_id=company_id,
                    key=key,
                    value=value,
                    value_type=value_type,
                    user_id=user_id,
                    username=username,
                )
            )
            uow.commit()
            return result

    def set_user_permissions(self, permissions: set[str]) -> None:
        """Atualiza as permissões do operador logado."""
        self._user_permissions = permissions
