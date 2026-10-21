from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Retorna um caminho de recurso em desenvolvimento ou no bundle PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        # src/erp/ui/resource_paths.py -> parents[2] = src
        base = Path(__file__).resolve().parents[2]

    return base.joinpath(*parts)
