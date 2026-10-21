"""Application services facade for Companies (use-case layer helpers)."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.companies.application.create_company import (
    CreateCompany,
    CreateCompanyInput,
    CreateCompanyOutput,
)
from erp.modules.companies.application.delete_company import (
    DeleteCompany,
    DeleteCompanyOutput,
)
from erp.modules.companies.application.get_company import GetCompany, GetCompanyOutput
from erp.modules.companies.application.list_active_companies import (
    ListActiveCompanies,
    ListActiveCompaniesOutput,
)
from erp.modules.companies.application.list_companies import (
    ListCompanies,
    ListCompaniesInput,
    ListCompaniesOutput,
)
from erp.modules.companies.application.permission_gate import CompanyPermissionGate
from erp.modules.companies.application.update_company import (
    UpdateCompany,
    UpdateCompanyInput,
    UpdateCompanyOutput,
)
from erp.modules.companies.infrastructure.unit_of_work import (
    SqlAlchemyCompanyUnitOfWork,
)


class CompaniesServices:
    """Fachada de casos de uso de empresa sobre SQLAlchemy (1 transação por operação)."""

    def __init__(
        self, engine: Engine, permission_gate: CompanyPermissionGate | None = None
    ) -> None:
        self._engine = engine
        self._permission_gate = permission_gate

    def _require_company_manage(self, actor_user_id: int | None) -> None:
        if self._permission_gate is not None and actor_user_id is not None:
            self._permission_gate.assert_can_manage_companies(actor_user_id)

    def create_company(
        self, input: CreateCompanyInput, *, actor_user_id: int | None = None
    ) -> CreateCompanyOutput:
        self._require_company_manage(actor_user_id)
        with SqlAlchemyCompanyUnitOfWork(self._engine) as uow:
            assert uow.companies is not None
            result = CreateCompany(uow.companies).execute(input)
            uow.commit()
            return result

    def list_companies(self, *, active_only: bool = False) -> ListCompaniesOutput:
        input_ = ListCompaniesInput(active_only=active_only)
        with SqlAlchemyCompanyUnitOfWork(self._engine) as uow:
            assert uow.companies is not None
            result = ListCompanies(uow.companies).execute(input_)
            uow.commit()
            return result

    def list_active_companies(self) -> ListActiveCompaniesOutput:
        with SqlAlchemyCompanyUnitOfWork(self._engine) as uow:
            assert uow.companies is not None
            result = ListActiveCompanies(uow.companies).execute()
            uow.commit()
            return result

    def get_company(self, company_id: int) -> GetCompanyOutput:
        with SqlAlchemyCompanyUnitOfWork(self._engine) as uow:
            assert uow.companies is not None
            output = GetCompany(uow.companies).execute(company_id)
            uow.commit()
            return output

    def update_company(
        self, input: UpdateCompanyInput, *, actor_user_id: int | None = None
    ) -> UpdateCompanyOutput:
        self._require_company_manage(actor_user_id)
        with SqlAlchemyCompanyUnitOfWork(self._engine) as uow:
            assert uow.companies is not None
            result = UpdateCompany(uow.companies).execute(input)
            uow.commit()
            return result

    def delete_company(
        self, company_id: int, *, actor_user_id: int | None = None
    ) -> DeleteCompanyOutput:
        self._require_company_manage(actor_user_id)
        with SqlAlchemyCompanyUnitOfWork(self._engine) as uow:
            assert uow.companies is not None
            result = DeleteCompany(uow.companies).execute(company_id)
            uow.commit()
            return result
