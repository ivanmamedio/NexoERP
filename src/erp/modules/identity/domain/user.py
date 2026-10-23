"""User entity with password policy and lockout after 5 failed attempts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from erp.shared.domain.entities import Entity


@dataclass(slots=True)
class User(Entity):
    """Usuário do sistema com controle de senha e bloqueio por tentativas falhas."""

    id: int | None = field(default=None)
    username: str = field(default="")
    password_hash: str = field(default="")
    must_change_password: bool = field(default=False)
    failed_login_attempts: int = field(default=0)
    locked_until: datetime | None = field(default=None)
    is_active: bool = field(default=True)
    company_id: int | None = field(default=None)
    roles: list[str] = field(default_factory=list)  # Carregado separadamente via repo.get_roles()

    def record_failed_login(self) -> None:
        """Incrementa tentativas falhas e bloqueia após 5."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(UTC) + timedelta(minutes=30)

    def reset_failed_logins(self) -> None:
        """Zera tentativas falhas após login bem-sucedido."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def is_locked(self) -> bool:
        """Retorna True se o usuário está bloqueado."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until
