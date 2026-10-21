"""Delete Company use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.shared.domain.errors import NotFound


class DeleteCompanyOutput:
    def __init__(self, company_id: int) -> None:
        self.company_id = company_id


class DeleteCompany:
    """Removes a Company from the repository."""

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def execute(self, company_id: int) -> DeleteCompanyOutput:
        company = self._repository.get_by_id(company_id)
        if company is None:
            raise NotFound(f"Empresa de id {company_id} não encontrada.")

        self._repository.delete(company_id)
        return DeleteCompanyOutput(company_id=company_id)
