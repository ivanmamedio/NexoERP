"""Bcrypt password hasher implementation."""

from __future__ import annotations

import logging

import bcrypt

from erp.modules.identity.application.ports import PasswordHasher

_logger = logging.getLogger(__name__)


class BcryptHasher(PasswordHasher):
    """Password hasher using bcrypt."""

    def hash(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            _logger.exception("Erro ao verificar hash de senha.")
            return False
