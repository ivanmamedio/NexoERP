"""Application module init for settings."""

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

__all__ = [
    "GetSetting",
    "GetSettingInput",
    "GetSettingOutput",
    "UpdateSetting",
    "UpdateSettingInput",
    "UpdateSettingOutput",
]
