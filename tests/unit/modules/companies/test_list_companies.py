"""Unit tests for ListCompanies use case."""

from __future__ import annotations

from erp.modules.companies.application.list_companies import ListCompanies, ListCompaniesInput
from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company


class FakeCompanyRepository(CompanyRepository):
    def __init__(self) -> None:
        self._companies = [
            Company(id=1, company_id=10, name="Ativa", trade_name="Ativa", tax_id="1", active=True),
            Company(id=2, company_id=10, name="Inativa", trade_name="Inativa", tax_id="2", active=False),
        ]
        self.added: list[Company] = []
        self.saved: list[Company] = []

    def add(self, company: Company) -> None:
        self.added.append(company)

    def save(self, company: Company) -> None:
        self.saved.append(company)

    def get_by_id(self, company_id: int) -> Company | None:
        raise NotImplementedError

    def get_by_tax_id(self, tax_id: str) -> Company | None:
        raise NotImplementedError

    def list_all(self) -> list[Company]:
        return list(self._companies)

    def delete(self, company_id: int) -> None:
        raise NotImplementedError


def test_list_companies_all() -> None:
    repo = FakeCompanyRepository()
    uc = ListCompanies(repo)

    output = uc.execute(ListCompaniesInput())

    assert len(output.companies) == 2
    assert {c.name for c in output.companies} == {"Ativa", "Inativa"}


def test_list_companies_active_only() -> None:
    repo = FakeCompanyRepository()
    uc = ListCompanies(repo)

    output = uc.execute(ListCompaniesInput(active_only=True))

    assert len(output.companies) == 1
    assert output.companies[0].name == "Ativa"
