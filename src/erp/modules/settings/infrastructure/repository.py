"""SQLAlchemy repositories for the settings module."""

from __future__ import annotations

from typing import cast

from sqlalchemy import select

from erp.modules.settings.application.ports import SettingsRepository
from erp.modules.settings.domain.setting import Setting
from erp.modules.settings.infrastructure.models import SettingModel
from erp.shared.infrastructure.repository import SqlAlchemyRepository


class SqlAlchemySettingsRepository(
    SqlAlchemyRepository[SettingModel, Setting, int], SettingsRepository
):
    """SQLAlchemy implementation of SettingsRepository."""

    _model_cls = SettingModel
    _company_id_column = "company_id"

    def _to_domain(self, model: SettingModel) -> Setting:
        return Setting(
            id=model.id,
            company_id=model.company_id,
            key=model.key,
            value=model.value,
            value_type=model.value_type,
            updated_at=model.updated_at,
            updated_by_user_id=model.updated_by_user_id,
            updated_by_username=model.updated_by_username,
        )

    def _to_model(self, domain: Setting) -> SettingModel:
        model = SettingModel()
        model.company_id = domain.company_id
        model.key = domain.key
        model.value = domain.value
        model.value_type = domain.value_type
        if domain.updated_at is not None:
            model.updated_at = domain.updated_at
        model.updated_by_user_id = domain.updated_by_user_id
        model.updated_by_username = domain.updated_by_username
        return model

    def get_by_key(self, *, company_id: int, key: str) -> Setting | None:
        stmt = select(SettingModel).where(
            SettingModel.company_id == company_id,
            SettingModel.key == key,
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_company(self, company_id: int) -> list[Setting]:
        stmt = (
            select(SettingModel)
            .where(SettingModel.company_id == company_id)
            .order_by(SettingModel.key)
        )
        models = self._session.execute(stmt).scalars().all()
        return cast(list[Setting], [self._to_domain(m) for m in models])

    def delete_by_key(self, key: str, company_id: int) -> None:
        stmt = select(SettingModel).where(
            SettingModel.company_id == company_id,
            SettingModel.key == key,
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is not None:
            self._session.delete(model)
            self._session.flush()
