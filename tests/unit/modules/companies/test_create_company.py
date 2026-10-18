"""Unit tests for CreateCompany use case."""

from __future__ import annotations

import pytest

from erp.modules.companies.application.create_company import CreateCompany, CreateCompanyInput
from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.shared.domain.errors import ValidationError


class FakeCompanyRepository(CompanyRepository):
    def __init__(self) -> None:
        self._companies: dict[int, Company] = {}
        self._by_tax_id: dict[str, Company] = {}
        self._next_id = 1

    def add(self, company: Company) -> None:
        if company.company_id is None:
            company.id = self._next_id
            company.company_id = self._next_id
            self._next_id += 1
        self._companies[company.company_id] = company
        self._by_tax_id[company.tax_id] = company

    def save(self, company: Company) -> None:
        self._companies[company.company_id] = company

    def get_by_id(self, company_id: int) -> Company | None:
        return self._companies.get(company_id)

    def get_by_tax_id(self, tax_id: str) -> Company | None:
        return self._by_tax_id.get(tax_id)

    def list_all(self) -> list[Company]:
        return list(self._companies.values())

    def delete(self, company_id: int) -> None:
        self._companies.pop(company_id, None)


def test_create_company_success() -> None:
    repo = FakeCompanyRepository()
    uc = CreateCompany(repo)

    output = uc.execute(
        CreateCompanyInput(
            name="ACME Ltda",
            trade_name="Acme",
            tax_id="12345678000190",
            address="Rua A",
            phone="11999999999",
            email="contato@acme.com",
            active=True,
        )
    )

    assert output.company.id is not None
    assert output.company.name == "ACME Ltda"
    assert output.company.company_id == 1

    stored = repo.get_by_tax_id("12345678000190")
    assert stored is not None
    assert stored.name == "ACME Ltda"


def test_create_company_duplicate_tax_id() -> None:
    repo = FakeCompanyRepository()
    uc = CreateCompany(repo)

    uc.execute(
        CreateCompanyInput(
            name="ACME Ltda",
            trade_name="Acme",
            tax_id="12345678000190",
            address="Rua A",
            email="contato@acme.com",
            active=True,
        )
    )

    with pytest.raises(ValidationError, match="CNPJ"):
        uc.execute(
            CreateCompanyInput(
                name="Outra",
                trade_name="Outra",
                tax_id="12345678000190",
                address="Rua B",
                email="outra@exemplo.com",
                active=True,
            )
        )


def test_create_company_empty_name() -> None:
    repo = FakeCompanyRepository()
    uc = CreateCompany(repo)

    with pytest.raises(ValidationError, match="obrigatório"):
        uc.execute(
            CreateCompanyInput(
                name="",
                trade_name="Outra",
                tax_id="12345678000191",
                address="Rua B",
                email="outra@exemplo.com",
                active=True,
            )
        )
