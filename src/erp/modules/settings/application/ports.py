"""Application ports for the settings module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.settings.domain.setting import Setting


@runtime_checkable
class SettingsRepository(Protocol):
    """Repository port for Setting aggregates."""

    def add(self, setting: Setting) -> None: ...
    def save(self, setting: Setting) -> None: ...
    def get_by_key(self, *, company_id: int, key: str) -> Setting | None: ...
    def list_by_company(self, company_id: int) -> list[Setting]: ...
    def delete_by_key(self, key: str, company_id: int) -> None: ...
