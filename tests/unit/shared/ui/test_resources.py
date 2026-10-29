"""Testes para resource_path (dev e bundle PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path

from erp.ui.resource_paths import resource_path


def test_resource_path_dev() -> None:
    """Em desenvolvimento, resolve relativo à pasta src."""
    path = resource_path("erp", "ui", "resources", "logo.png")
    assert path.is_absolute()
    assert path.name == "logo.png"
    assert path.exists()


def test_resource_path_frozen(monkeypatch) -> None:
    """No bundle PyInstaller, resolve relativo a sys._MEIPASS."""
    fake_meipass = "/tmp/fake_meipass"
    # Simula ambiente congelado (PyInstaller define sys.frozen)
    sys_module = sys
    sys_module.frozen = True  # type: ignore[attr-defined]
    sys_module._MEIPASS = fake_meipass  # type: ignore[attr-defined]

    try:
        # O módulo usa sys diretamente, não precisa recarregar
        path = resource_path("erp", "ui", "resources", "logo.png")
        assert str(path).startswith(fake_meipass + "/erp")
        assert path.name == "logo.png"
    finally:
        del sys_module.frozen  # type: ignore[attr-defined]
        del sys_module._MEIPASS  # type: ignore[attr-defined]


def test_resource_path_missing_file_still_returns_path() -> None:
    """resource_path não lança exceção mesmo se o arquivo não existir."""
    path = resource_path("arquivo", "inexistente", "nao_existe.png")
    assert isinstance(path, Path)
