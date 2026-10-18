"""Get Company use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.shared.domain.errors import NotFound


class GetCompanyOutput:
    def __init__(self, company: Company) -> None:
        self.company = company


class GetCompany:
    """Retrieves a Company by id."""

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def execute(self, company_id: int) -> GetCompanyOutput:
        company = self._repository.get_by_id(company_id)
        if company is None:
            raise NotFound(f"Empresa de id {company_id} não encontrada.")
        return GetCompanyOutput(company=company)
