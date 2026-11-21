"""Create Company use case."""

from __future__ import annotations

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.shared.domain.cnpj import is_valid_cnpj, normalize_cnpj
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

        # Normalize CNPJ (remove non-digits)
        normalized_tax_id = normalize_cnpj(input.tax_id)

        # Validate CNPJ format (must be 14 digits)
        if len(normalized_tax_id) != 14:
            raise ValidationError("CNPJ inválido. Deve conter 14 dígitos numéricos.")

        # Validate CNPJ using modulus 11 algorithm
        if not is_valid_cnpj(normalized_tax_id):
            raise ValidationError("CNPJ inválido.")

        existing = self._repository.get_by_tax_id(normalized_tax_id)
        if existing is not None:
            # Format for display in error message
            formatted_tax_id = normalized_tax_id[:2] + "." + normalized_tax_id[2:5] + "." + normalized_tax_id[5:8] + "/" + normalized_tax_id[8:12] + "-" + normalized_tax_id[12:]
            raise ValidationError(f"Já existe uma empresa cadastrada com o CNPJ {formatted_tax_id}.")

        company = Company(
            name=input.name.strip(),
            trade_name=input.trade_name.strip(),
            tax_id=normalized_tax_id,
            address=input.address,
            phone=input.phone,
            email=input.email,
            active=input.active,
        )
        self._repository.add(company)
        return CreateCompanyOutput(company=company)
