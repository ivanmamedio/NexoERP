"""Unit tests for GetCompany use case."""

from __future__ import annotations

import pytest

from erp.modules.companies.application.get_company import GetCompany
from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.shared.domain.errors import NotFound


class FakeCompanyRepository(CompanyRepository):
    def __init__(self) -> None:
        self._companies = {
            1: Company(id=1, company_id=10, name="Ativa", trade_name="Ativa", tax_id="1", active=True),
            2: Company(id=2, company_id=10, name="Inativa", trade_name="Inativa", tax_id="2", active=False),
        }

    def add(self, company: Company) -> None:
        raise NotImplementedError

    def save(self, company: Company) -> None:
        raise NotImplementedError

    def get_by_id(self, company_id: int) -> Company | None:
        return self._companies.get(company_id)

    def get_by_tax_id(self, tax_id: str) -> Company | None:
        raise NotImplementedError

    def list_all(self) -> list[Company]:
        raise NotImplementedError

    def delete(self, company_id: int) -> None:
        raise NotImplementedError


def test_get_company_success() -> None:
    repo = FakeCompanyRepository()
    uc = GetCompany(repo)

    output = uc.execute(1)

    assert output.company.id == 1
    assert output.company.name == "Ativa"


def test_get_company_not_found() -> None:
    repo = FakeCompanyRepository()
    uc = GetCompany(repo)

    with pytest.raises(NotFound, match="não encontrada"):
        uc.execute(99)
