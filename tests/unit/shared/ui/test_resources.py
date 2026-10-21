"""Testes para resource_path (dev e bundle PyInstaller)."""

from __future__ import annotations

from erp.shared.ui.resources import resource_path


def test_resource_path_dev() -> None:
    """Em desenvolvimento, resolve relativo à pasta do pacote erp."""
    path = resource_path("ui", "resources", "logo.png")
    assert path.is_absolute()
    assert path.name == "logo.png"
    assert path.exists()


def test_resource_path_frozen(monkeypatch) -> None:
    """No bundle PyInstaller, resolve relativo a sys._MEIPASS/erp."""
    fake_meipass = "/tmp/fake_meipass"
    # Simula ambiente congelado (PyInstaller define sys.frozen)
    sys_module = __import__("sys")
    sys_module.frozen = True  # type: ignore[attr-defined]
    sys_module._MEIPASS = fake_meipass  # type: ignore[attr-defined]

    try:
        # Recarrega o módulo para pegar a nova sys._MEIPASS
        import importlib

        import erp.shared.ui.resources as resources_mod

        importlib.reload(resources_mod)

        path = resources_mod.resource_path("ui", "resources", "logo.png")
        assert str(path).startswith(fake_meipass + "/erp")
        assert path.name == "logo.png"
    finally:
        del sys_module.frozen  # type: ignore[attr-defined]
        del sys_module._MEIPASS  # type: ignore[attr-defined]


def test_resource_path_missing_file_still_returns_path() -> None:
    """resource_path não lança exceção mesmo se o arquivo não existir."""
    path = resource_path("arquivo", "inexistente", "nao_existe.png")
    assert isinstance(path, __import__("pathlib").Path)
