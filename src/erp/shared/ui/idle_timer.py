"""Sessão ociosa: fecha a sessão após N minutos sem atividade do usuário.

Lógica pura (sem Qt) para facilitar testes; a UI registra a atividade via
``register_activity`` (conectado a eventos de mouse/teclado) e observa
``is_expired``/o callback ``on_expired`` configurado pela janela principal.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class IdleSessionTimer:
    """Controla o timeout de sessão ociosa com clock injetável."""

    def __init__(
        self,
        timeout_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser positivo")
        self._timeout_seconds = timeout_seconds
        self._clock = clock
        self._last_activity = clock()

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    def register_activity(self) -> None:
        """Registra atividade do usuário, reiniciando a contagem."""
        self._last_activity = self._clock()

    def seconds_until_expiry(self) -> float:
        """Segundos restantes até a sessão expirar (nunca negativo)."""
        elapsed = self._clock() - self._last_activity
        return max(0.0, self._timeout_seconds - elapsed)

    def is_expired(self) -> bool:
        """True se o usuário ficou ocioso além do timeout."""
        return self.seconds_until_expiry() <= 0.0
