"""Create Company use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.shared.domain.errors import ValidationError


class CreateCompanyInput:
    def __init__(
        self,
        *,
        name: str,
        trade_name: str,
        tax_id: str,
        address: str = "",
        phone: str = "",
        email: str = "",
        active: bool = True,
    ) -> None:
        self.name = name
        self.trade_name = trade_name
        self.tax_id = tax_id
        self.address = address
        self.phone = phone
        self.email = email
        self.active = active


class CreateCompanyOutput:
    def __init__(self, company: Company) -> None:
        self.company = company


class CreateCompany:
    """Creates a new Company.

    Validates uniqueness of tax_id and required fields.
    """

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def execute(self, input: CreateCompanyInput) -> CreateCompanyOutput:
        if not input.name:
            raise ValidationError("Nome da empresa é obrigatório.")

        existing = self._repository.get_by_tax_id(input.tax_id)
        if existing is not None:
            raise ValidationError(f"Já existe uma empresa cadastrada com o CNPJ {input.tax_id}.")

        company = Company(
            name=input.name.strip(),
            trade_name=input.trade_name.strip(),
            tax_id=input.tax_id.strip(),
            address=input.address,
            phone=input.phone,
            email=input.email,
            active=input.active,
        )
        self._repository.add(company)
        return CreateCompanyOutput(company=company)
