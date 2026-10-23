from dataclasses import dataclass

from erp.shared.domain.errors import DomainError


@dataclass
class CurrentSession:
    user_id: int | None = None
    user_number: int | None = None
    company_id: int | None = None
    username: str | None = None

    def is_authenticated(self) -> bool:
        return self.user_id is not None

    def require_company(self) -> int:
        if self.company_id is None:
            raise DomainError("Nenhuma empresa ativa na sessao.")
        return self.company_id
