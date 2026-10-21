"""Password policy for user creation and password changes."""

from __future__ import annotations

import re

# Mínimo de caracteres exigidos
MIN_PASSWORD_LENGTH = 8
# Pelo menos uma letra e um dígito
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


def validate_password_policy(password: str) -> None:
    """Valida a senha contra a política.

    Regras:
    - no mínimo 8 caracteres
    - pelo menos uma letra e um dígito

    Levanta ValueError com mensagem clara caso a senha não atenda.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres")
    if not _PASSWORD_RE.match(password):
        raise ValueError("A senha deve conter pelo menos uma letra e um dígito")
