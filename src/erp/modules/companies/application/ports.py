"""Ports (interfaces) for companies application layer."""

from typing import Protocol, runtime_checkable

from erp.modules.companies.domain.company import Company
from erp.modules.identity.domain.user import User


@runtime_checkable
class CompanyRepository(Protocol):
    """Repository port for Company aggregates."""

    def add(self, company: Company) -> None: ...

    def save(self, company: Company) -> None: ...

    def get_by_id(self, company_id: int) -> Company | None: ...

    def get_by_tax_id(self, tax_id: str) -> Company | None: ...

    def list_all(self, *, company_id: int | None = None) -> list[Company]: ...

    def delete(self, company_id: int) -> None: ...


@runtime_checkable
class PermissionCheckerPort(Protocol):
    """Port for checking user permissions (implemented by identity module)."""

    def has_permission(self, user: User, permission_code: str) -> bool: ...
