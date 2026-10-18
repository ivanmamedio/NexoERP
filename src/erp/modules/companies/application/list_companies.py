"""List Companies use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company


class ListCompaniesInput:
    def __init__(self, *, active_only: bool = False) -> None:
        self.active_only = active_only


class ListCompaniesOutput:
    def __init__(self, companies: list[Company]) -> None:
        self.companies = companies


class ListCompanies:
    """Lists companies."""

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def execute(self, input: ListCompaniesInput) -> ListCompaniesOutput:
        companies = self._repository.list_all()
        if input.active_only:
            companies = [c for c in companies if c.active]
        return ListCompaniesOutput(companies=companies)
