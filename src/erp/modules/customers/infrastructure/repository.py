"""SQLAlchemy repositories for the customers module."""

from __future__ import annotations

from typing import cast

from sqlalchemy import select

from erp.modules.customers.application.ports import CustomerRepository
from erp.modules.customers.domain.customer import Customer
from erp.modules.customers.infrastructure.models import CustomerModel
from erp.shared.infrastructure.repository import SqlAlchemyRepository


class SqlAlchemyCustomerRepository(
    SqlAlchemyRepository[CustomerModel, Customer, int], CustomerRepository
):
    """SQLAlchemy implementation of CustomerRepository."""

    _model_cls = CustomerModel

    def _to_domain(self, model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            phone=model.phone,
            document=model.document,
            credit_limit_cents=model.credit_limit_cents,
            is_active=model.is_active,
        )

    def _to_model(self, domain: Customer) -> CustomerModel:
        model = CustomerModel()
        model.company_id = domain.company_id
        model.name = domain.name
        model.phone = domain.phone
        model.document = domain.document
        model.credit_limit_cents = domain.credit_limit_cents
        model.is_active = domain.is_active
        return model

    def get_by_phone(self, phone: str, company_id: int) -> Customer | None:
        stmt = select(CustomerModel).where(
            CustomerModel.phone == phone,
            CustomerModel.company_id == company_id,
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_company(
        self,
        company_id: int,
        name_contains: str | None = None,
    ) -> list[Customer]:
        stmt = select(CustomerModel).where(CustomerModel.company_id == company_id)
        if name_contains:
            stmt = stmt.where(CustomerModel.name.ilike(f"%{name_contains}%"))
        models = self._session.execute(stmt).scalars().all()
        return cast(list[Customer], [self._to_domain(m) for m in models])
