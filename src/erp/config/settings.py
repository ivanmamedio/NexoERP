"""Configurações gerais da aplicação (lidas de variáveis de ambiente)."""

from __future__ import annotations

import os

DEFAULT_SESSION_TIMEOUT_MINUTES = 15


def get_session_timeout_minutes() -> int:
    """Retorna o timeout de sessão ociosa em minutos.

    Configurável via variável de ambiente ``NEXOERP_SESSION_TIMEOUT_MINUTES``.
    Valores ausentes ou inválidos usam o padrão (15 minutos).
    """
    raw = os.environ.get("NEXOERP_SESSION_TIMEOUT_MINUTES", "")
    try:
        minutes = int(raw)
    except ValueError:
        return DEFAULT_SESSION_TIMEOUT_MINUTES
    return minutes if minutes >= 1 else DEFAULT_SESSION_TIMEOUT_MINUTES
