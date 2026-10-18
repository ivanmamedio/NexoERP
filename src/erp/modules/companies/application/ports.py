"""Ports (interfaces) for companies application layer."""

from typing import Protocol, runtime_checkable

from erp.modules.companies.domain.company import Company


@runtime_checkable
class CompanyRepository(Protocol):
    """Repository port for Company aggregates."""

    def add(self, company: Company) -> None: ...

    def save(self, company: Company) -> None: ...

    def get_by_id(self, company_id: int) -> Company | None: ...

    def get_by_tax_id(self, tax_id: str) -> Company | None: ...

    def list_all(self) -> list[Company]: ...

    def delete(self, company_id: int) -> None: ...
