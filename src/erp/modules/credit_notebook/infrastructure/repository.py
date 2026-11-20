"""SQLAlchemy repositories for the credit notebook module."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from erp.modules.credit_notebook.application.ports import (
    CreditCustomerRepository,
    CreditEntryRepository,
)
from erp.modules.credit_notebook.domain.credit_customer import CreditCustomer
from erp.modules.credit_notebook.domain.credit_entry import CreditEntry
from erp.modules.credit_notebook.infrastructure.models import (
    CreditCustomerModel,
    CreditEntryModel,
)
from erp.shared.application.session import CurrentSession


class SqlAlchemyCreditCustomerRepository(CreditCustomerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, customer: CreditCustomer) -> None:
        model = CreditCustomerModel()
        model.company_id = customer.company_id or CurrentSession().company_id
        model.name = customer.name
        model.phone = customer.phone
        model.email = customer.email
        model.address = customer.address
        model.notes = customer.notes
        model.credit_limit_cents = customer.credit_limit_cents
        model.status = customer.status
        self._session.add(model)
        self._session.flush()
        customer.id = model.id

    def save(self, customer: CreditCustomer) -> None:
        if customer.id is None:
            raise ValueError("Customer must have an id to update")
        model = self._session.get(CreditCustomerModel, customer.id)
        if model is None:
            raise ValueError(f"Customer {customer.id} not found")
        model.name = customer.name
        model.phone = customer.phone
        model.email = customer.email
        model.address = customer.address
        model.notes = customer.notes
        model.credit_limit_cents = customer.credit_limit_cents
        model.status = customer.status
        model.updated_at = customer.updated_at
        self._session.add(model)
        self._session.flush()

    def get_by_id(self, customer_id: int) -> CreditCustomer | None:
        model = self._session.get(CreditCustomerModel, customer_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_phone(self, phone: str, company_id: int | None = None) -> CreditCustomer | None:
        stmt = select(CreditCustomerModel).where(CreditCustomerModel.phone == phone)
        if company_id is not None:
            stmt = stmt.where(CreditCustomerModel.company_id == company_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def search(
        self, query: str, company_id: int | None = None, limit: int = 50
    ) -> list[CreditCustomer]:
        stmt = select(CreditCustomerModel).where(
            or_(
                CreditCustomerModel.name.ilike(f"%{query}%"),
                CreditCustomerModel.phone.ilike(f"%{query}%"),
                CreditCustomerModel.email.ilike(f"%{query}%"),
            )
        )
        cid = company_id if company_id is not None else CurrentSession().company_id
        if cid is not None:
            stmt = stmt.where(CreditCustomerModel.company_id == cid)
        stmt = stmt.limit(limit)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def list_all(
        self, company_id: int | None = None, status: str | None = None
    ) -> list[CreditCustomer]:
        stmt = select(CreditCustomerModel)
        cid = company_id if company_id is not None else CurrentSession().company_id
        if cid is not None:
            stmt = stmt.where(CreditCustomerModel.company_id == cid)
        if status is not None:
            stmt = stmt.where(CreditCustomerModel.status == status)
        stmt = stmt.order_by(CreditCustomerModel.name)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: CreditCustomerModel) -> CreditCustomer:
        return CreditCustomer(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            phone=model.phone,
            email=model.email,
            address=model.address,
            notes=model.notes,
            credit_limit_cents=model.credit_limit_cents,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyCreditEntryRepository(CreditEntryRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: CreditEntry) -> None:
        model = CreditEntryModel()
        model.customer_id = entry.customer_id
        model.company_id = entry.company_id or CurrentSession().company_id
        model.entry_type = entry.entry_type
        model.description = entry.description
        model.amount_cents = entry.amount_cents
        model.status = entry.status
        model.due_date = entry.due_date
        model.paid_at = entry.paid_at
        model.paid_amount_cents = entry.paid_amount_cents
        model.reference_type = entry.reference_type
        model.reference_id = entry.reference_id
        model.notes = entry.notes
        model.created_by_user_id = entry.created_by_user_id
        model.created_by_username = entry.created_by_username
        self._session.add(model)
        self._session.flush()
        entry.id = model.id

    def save(self, entry: CreditEntry) -> None:
        if entry.id is None:
            raise ValueError("Entry must have an id to update")
        model = self._session.get(CreditEntryModel, entry.id)
        if model is None:
            raise ValueError(f"Entry {entry.id} not found")
        model.status = entry.status
        model.paid_at = entry.paid_at
        model.paid_amount_cents = entry.paid_amount_cents
        self._session.add(model)
        self._session.flush()

    def get_by_id(self, entry_id: int) -> CreditEntry | None:
        model = self._session.get(CreditEntryModel, entry_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_customer(self, customer_id: int, status: str | None = None) -> list[CreditEntry]:
        stmt = select(CreditEntryModel).where(CreditEntryModel.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(CreditEntryModel.status == status)
        stmt = stmt.order_by(CreditEntryModel.created_at.desc())
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def list_by_company(
        self, company_id: int | None = None, status: str | None = None
    ) -> list[CreditEntry]:
        stmt = select(CreditEntryModel)
        cid = company_id if company_id is not None else CurrentSession().company_id
        if cid is not None:
            stmt = stmt.where(CreditEntryModel.company_id == cid)
        if status is not None:
            stmt = stmt.where(CreditEntryModel.status == status)
        stmt = stmt.order_by(CreditEntryModel.created_at.desc())
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def get_pending_by_customer(self, customer_id: int) -> list[CreditEntry]:
        stmt = select(CreditEntryModel).where(
            CreditEntryModel.customer_id == customer_id,
            CreditEntryModel.status.in_(["pending", "partial"]),
        )
        stmt = stmt.order_by(
            CreditEntryModel.due_date.asc().nulls_last(), CreditEntryModel.created_at
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: CreditEntryModel) -> CreditEntry:
        return CreditEntry(
            id=model.id,
            customer_id=model.customer_id,
            company_id=model.company_id,
            entry_type=model.entry_type,
            description=model.description,
            amount_cents=model.amount_cents,
            status=model.status,
            due_date=model.due_date,
            paid_at=model.paid_at,
            paid_amount_cents=model.paid_amount_cents,
            reference_type=model.reference_type,
            reference_id=model.reference_id,
            notes=model.notes,
            created_by_user_id=model.created_by_user_id,
            created_by_username=model.created_by_username,
            created_at=model.created_at,
        )
