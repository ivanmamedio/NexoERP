"""Password policy for user creation and password changes."""

from __future__ import annotations

import re

# Mínimo de caracteres exigidos
MIN_PASSWORD_LENGTH = 8
# Bcrypt truncates passwords at 72 bytes (not chars), so we limit to 72 chars
# to be safe (UTF-8 multi-byte chars could exceed 72 bytes)
MAX_PASSWORD_LENGTH = 72
# Pelo menos uma letra e um dígito
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


def validate_password_policy(password: str) -> None:
    """Valida a senha contra a política.

    Regras:
    - no mínimo 8 caracteres
    - no máximo 72 caracteres (limite do bcrypt)
    - pelo menos uma letra e um dígito

    Levanta ValueError com mensagem clara caso a senha não atenda.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"A senha deve ter no máximo {MAX_PASSWORD_LENGTH} caracteres")
    if not _PASSWORD_RE.match(password):
        raise ValueError("A senha deve conter pelo menos uma letra e um dígito")
