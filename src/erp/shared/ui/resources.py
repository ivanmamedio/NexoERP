"""Resolução de caminhos de recursos (imagens, ícones, etc.).

Funciona tanto em desenvolvimento quanto no bundle do PyInstaller.

Este módulo re-exporta o helper canônico de ``erp.ui.resource_paths``
para manter compatibilidade com código existente.
"""

from __future__ import annotations

from erp.ui.resource_paths import resource_path

__all__ = ["resource_path"]
