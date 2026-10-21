"""Resolução de caminhos de recursos (imagens, ícones, etc.).

Funciona tanto em desenvolvimento quanto no bundle do PyInstaller.

Quando congelado, os recursos ficam em ``sys._MEIPASS/erp`` (o pacote
``erp`` é copiado para a raiz do bundle). Em desenvolvimento, usamos a
pasta do próprio pacote ``erp``.
"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Retorna o caminho absoluto para um recurso do pacote ``erp``.

    Em desenvolvimento, resolve relativo à pasta do pacote ``erp``.
    No bundle PyInstaller (``sys.frozen``), resolve relativo a
    ``sys._MEIPASS/erp``.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS) / "erp"
    else:
        # src/erp/shared/ui/resources.py -> parents[2] = pasta do pacote erp
        base = Path(__file__).resolve().parents[2]

    return base.joinpath(*parts)
