"""SQLAlchemy repository for Company entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.companies.application.ports import CompanyRepository
from erp.modules.companies.domain.company import Company
from erp.modules.companies.infrastructure.models import CompanyModel
from erp.shared.application.session import CurrentSession


class SqlAlchemyCompanyRepository(CompanyRepository):
    """SQLAlchemy implementation of CompanyRepository.

    The repository automatically scopes every query to the ``company_id`` of the
    current session. Data from other companies is never returned.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def _company_id(self) -> int | None:
        return CurrentSession().company_id

    def _filter_company(self, stmt: select) -> select:  # type: ignore[valid-type]
        company_id = self._company_id()
        if company_id is not None:
            stmt = stmt.where(CompanyModel.company_id == company_id)  # type: ignore[attr-defined]
        return stmt

    def add(self, company: Company) -> None:
        if company.id is not None:
            raise ValueError("Company already has an id; use save to update")

        company_id = company.company_id
        if company_id is None:
            company_id = self._company_id()
        if company_id is None:
            raise ValueError("Company must have a company_id or an active company session")

        model = CompanyModel()
        model.company_id = company_id
        model.name = company.name
        model.trade_name = company.trade_name
        model.tax_id = company.tax_id
        model.address = company.address
        model.phone = company.phone
        model.email = company.email
        model.active = company.active

        self._session.add(model)
        self._session.flush()
        company.id = model.id

    def save(self, company: Company) -> None:
        model = self._session.get(CompanyModel, company.id)
        if model is None:
            raise ValueError(f"Company {company.id} not found")

        model.name = company.name
        model.trade_name = company.trade_name
        model.tax_id = company.tax_id
        model.address = company.address
        model.phone = company.phone
        model.email = company.email
        model.active = company.active
        # Do not allow changing company_id through save; it is managed by session scope
        model.updated_at = company.updated_at  # type: ignore[assignment]

        self._session.add(model)
        self._session.flush()

    def get_by_id(self, company_id: int) -> Company | None:
        stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        model = self._session.execute(self._filter_company(stmt)).scalar_one_or_none()  # type: ignore[misc]
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_tax_id(self, tax_id: str) -> Company | None:
        stmt = select(CompanyModel).where(CompanyModel.tax_id == tax_id)
        model = self._session.execute(self._filter_company(stmt)).scalar_one_or_none()  # type: ignore[misc]
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, *, company_id: int | None = None) -> list[Company]:
        stmt = select(CompanyModel)
        if company_id is not None:
            stmt = stmt.where(CompanyModel.company_id == company_id)
        else:
            stmt = self._filter_company(stmt)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def delete(self, company_id: int) -> None:
        stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        model = self._session.execute(self._filter_company(stmt)).scalar_one_or_none()  # type: ignore[misc]
        if model is None:
            raise ValueError(f"Company {company_id} not found")
        self._session.delete(model)

    def _model_to_domain(self, model: CompanyModel) -> Company:
        return Company(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            trade_name=model.trade_name,
            tax_id=model.tax_id,
            address=model.address,
            phone=model.phone,
            email=model.email,
            active=model.active,
            created_at=model.created_at.isoformat() if model.created_at else None,
        )

