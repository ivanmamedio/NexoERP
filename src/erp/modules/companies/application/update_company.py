"""Update Company use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.shared.domain.errors import NotFound


class UpdateCompanyInput:
    def __init__(
        self,
        *,
        company_id: int,
        name: str,
        trade_name: str,
        tax_id: str,
        address: str = "",
        phone: str = "",
        email: str = "",
        active: bool = True,
    ) -> None:
        self.company_id = company_id
        self.name = name
        self.trade_name = trade_name
        self.tax_id = tax_id
        self.address = address
        self.phone = phone
        self.email = email
        self.active = active


class UpdateCompanyOutput:
    def __init__(self, company: Company) -> None:
        self.company = company


class UpdateCompany:
    """Updates a Company."""

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def execute(self, input: UpdateCompanyInput) -> UpdateCompanyOutput:
        company = self._repository.get_by_id(input.company_id)
        if company is None:
            raise NotFound(f"Empresa de id {input.company_id} não encontrada.")

        if not input.name:
            raise ValueError("Nome da empresa é obrigatório.")

        # Atualiza apenas os campos fornecidos (mantendo ids/enums/qualities).
        company.name = input.name.strip()
        company.trade_name = input.trade_name.strip()
        company.tax_id = input.tax_id.strip()
        company.address = input.address
        company.phone = input.phone
        company.email = input.email
        company.active = input.active

        self._repository.save(company)
        return UpdateCompanyOutput(company=company)

