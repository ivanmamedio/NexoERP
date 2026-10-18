"""List Active Companies use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company


class ListActiveCompaniesOutput:
    def __init__(self, companies: list[Company]) -> None:
        self.companies = companies


class ListActiveCompanies:
    """Lists active companies."""

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def execute(self) -> ListActiveCompaniesOutput:
        companies = self._repository.list_all()
        return ListActiveCompaniesOutput(companies=[c for c in companies if c.active])
