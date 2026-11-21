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

    Companies are global entities (CNPJ is unique globally).
    The `company_id` column is a self-referential FK for hierarchical companies (parent company),
    NOT a tenant scope. Top-level companies have company_id = NULL.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, company: Company) -> None:
        if company.id is not None:
            raise ValueError("Company already has an id; use save to update")

        # company_id is the parent company (self-referential), NOT tenant scope.
        # Top-level companies have company_id = None.
        model = CompanyModel()
        model.company_id = company.company_id  # Can be None for top-level companies
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
        # company_id (parent company) can be changed through save if needed
        model.company_id = company.company_id
        model.updated_at = company.updated_at  # type: ignore[assignment]

        self._session.add(model)
        self._session.flush()

    def get_by_id(self, company_id: int) -> Company | None:
        stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_tax_id(self, tax_id: str) -> Company | None:
        """Check CNPJ uniqueness GLOBALLY (not scoped to tenant).
        
        tax_id has unique=True constraint in database, so this must be a global check.
        """
        stmt = select(CompanyModel).where(CompanyModel.tax_id == tax_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, *, company_id: int | None = None) -> list[Company]:
        """List companies, optionally filtered by parent company_id (for hierarchical queries).
        
        This is NOT tenant filtering - it's for querying company hierarchies.
        """
        stmt = select(CompanyModel)
        if company_id is not None:
            stmt = stmt.where(CompanyModel.company_id == company_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def delete(self, company_id: int) -> None:
        stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        model = self._session.execute(stmt).scalar_one_or_none()
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
