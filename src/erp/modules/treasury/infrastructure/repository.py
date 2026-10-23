"""SQLAlchemy repositories for treasury module."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.treasury.application.ports import (
    FinancialCategoryRepository,
    FinancialEntryRepository,
    PayableRepository,
    ReceivableRepository,
)
from erp.modules.treasury.domain.financial_category import FinancialCategory
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.domain.payable import Payable, PayableInstallment
from erp.modules.treasury.domain.receivable import Receivable
from erp.modules.treasury.infrastructure.models import (
    FinancialCategoryModel,
    FinancialEntryModel,
    PayableInstallmentModel,
    PayableModel,
    ReceivableModel,
)


class SqlAlchemyFinancialEntryRepository(FinancialEntryRepository):
    """SQLAlchemy repository for financial entries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: FinancialEntry) -> None:
        now = entry.date if entry.date is not None else datetime.now(UTC)
        model = FinancialEntryModel()
        model.company_id = entry.company_id
        model.date = now
        model.type = entry.type
        model.amount_cents = entry.amount_cents
        model.category_id = entry.category_id
        model.source_type = entry.source_type
        model.source_id = entry.source_id
        model.description = entry.description
        self._session.add(model)
        self._session.flush()
        entry.id = model.id

    def list_by_company(self, company_id: int | None = None) -> list[FinancialEntry]:
        stmt = select(FinancialEntryModel)
        if company_id is not None:
            stmt = stmt.where(FinancialEntryModel.company_id == company_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def list_by_period(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
    ) -> list[FinancialEntry]:
        stmt = select(FinancialEntryModel).where(
            FinancialEntryModel.date >= start_date,
            FinancialEntryModel.date <= end_date,
        )
        if company_id is not None:
            stmt = stmt.where(FinancialEntryModel.company_id == company_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: FinancialEntryModel) -> FinancialEntry:
        return FinancialEntry(
            id=model.id,
            company_id=model.company_id,
            date=model.date,
            type=model.type,
            amount_cents=model.amount_cents,
            category_id=model.category_id,
            source_type=model.source_type,
            source_id=model.source_id,
            description=model.description,
        )


class SqlAlchemyFinancialCategoryRepository(FinancialCategoryRepository):
    """SQLAlchemy repository for financial categories."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, category: FinancialCategory) -> None:
        model = FinancialCategoryModel()
        model.company_id = category.company_id
        model.name = category.name
        model.kind = category.kind
        model.description = category.description
        model.is_active = category.is_active
        self._session.add(model)
        self._session.flush()
        category.id = model.id

    def get_by_id(self, category_id: int) -> FinancialCategory | None:
        model = self._session.get(FinancialCategoryModel, category_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_name(self, name: str, company_id: int | None = None) -> FinancialCategory | None:
        stmt = select(FinancialCategoryModel).where(FinancialCategoryModel.name == name)
        if company_id is not None:
            stmt = stmt.where(FinancialCategoryModel.company_id == company_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, company_id: int | None = None) -> list[FinancialCategory]:
        stmt = select(FinancialCategoryModel)
        if company_id is not None:
            stmt = stmt.where(FinancialCategoryModel.company_id == company_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def save(self, category: FinancialCategory) -> None:
        model = self._session.get(FinancialCategoryModel, category.id)
        if model is None:
            raise ValueError(f"Category {category.id} not found")
        model.name = category.name
        model.kind = category.kind
        model.description = category.description
        model.is_active = category.is_active
        self._session.flush()

    def delete(self, category_id: int) -> None:
        model = self._session.get(FinancialCategoryModel, category_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()

    def _model_to_domain(self, model: FinancialCategoryModel) -> FinancialCategory:
        return FinancialCategory(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            kind=model.kind,
            description=model.description,
            is_active=model.is_active,
        )


class SqlAlchemyPayableRepository(PayableRepository):
    """SQLAlchemy repository for payables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, payable: Payable) -> None:
        model = self._to_model(payable)
        # Add installments to the model's relationship
        for inst in payable.installments:
            inst_model = self._installment_to_model(inst)
            model.installments.append(inst_model)
        self._session.add(model)
        self._session.flush()
        payable.id = model.id
        # Update domain installments with generated IDs
        for i, inst_model in enumerate(model.installments):
            if i < len(payable.installments):
                payable.installments[i].id = inst_model.id

    def get_by_id(self, payable_id: int) -> Payable | None:
        model = self._session.get(PayableModel, payable_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(
        self, company_id: int | None = None, status: str | None = None
    ) -> list[Payable]:
        stmt = select(PayableModel)
        if company_id is not None:
            stmt = stmt.where(PayableModel.company_id == company_id)
        if status is not None:
            stmt = stmt.where(PayableModel.status == status)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def save(self, payable: Payable) -> None:
        model = self._session.get(PayableModel, payable.id)
        if model is None:
            self.add(payable)
            return
        self._update_model(model, payable)
        self._session.flush()

    def _to_model(self, payable: Payable) -> PayableModel:
        model = PayableModel()
        model.company_id = payable.company_id
        model.supplier_id = payable.supplier_id
        model.category_id = payable.category_id
        model.description = payable.description
        model.total_amount_cents = payable.total_amount_cents
        model.status = payable.status
        model.issue_date = payable.issue_date
        model.recurrence_type = payable.recurrence_type
        model.recurrence_count = payable.recurrence_count
        model.source_type = payable.source_type
        model.source_id = payable.source_id
        # Installments will be added via relationship
        return model

    def _update_model(self, model: PayableModel, payable: Payable) -> None:
        model.supplier_id = payable.supplier_id
        model.category_id = payable.category_id
        model.description = payable.description
        model.total_amount_cents = payable.total_amount_cents
        model.status = payable.status
        model.recurrence_type = payable.recurrence_type
        model.recurrence_count = payable.recurrence_count
        model.source_type = payable.source_type
        model.source_id = payable.source_id

    def _model_to_domain(self, model: PayableModel) -> Payable:
        payable = Payable(
            id=model.id,
            company_id=model.company_id,
            supplier_id=model.supplier_id,
            category_id=model.category_id,
            description=model.description,
            total_amount_cents=model.total_amount_cents,
            status=model.status,
            issue_date=model.issue_date,
            recurrence_type=model.recurrence_type,
            recurrence_count=model.recurrence_count,
            source_type=model.source_type,
            source_id=model.source_id,
        )
        # Installments will be loaded via relationship
        payable.installments = [self._installment_to_domain(i) for i in model.installments]
        return payable

    def _installment_to_domain(self, model: PayableInstallmentModel) -> PayableInstallment:
        return PayableInstallment(
            id=model.id,
            payable_id=model.payable_id,
            installment_number=model.installment_number,
            due_date=model.due_date,
            amount_cents=model.amount_cents,
            status=model.status,
            paid_at=model.paid_at,
            paid_amount_cents=model.paid_amount_cents,
        )

    def _installment_to_model(self, installment: PayableInstallment) -> PayableInstallmentModel:
        model = PayableInstallmentModel()
        model.installment_number = installment.installment_number
        model.due_date = installment.due_date
        model.amount_cents = installment.amount_cents
        model.status = installment.status
        model.paid_at = installment.paid_at
        model.paid_amount_cents = installment.paid_amount_cents
        return model


class SqlAlchemyReceivableRepository(ReceivableRepository):
    """SQLAlchemy repository for receivables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, receivable: Receivable) -> None:
        model = ReceivableModel()
        model.company_id = receivable.company_id
        model.customer_id = receivable.customer_id
        model.category_id = receivable.category_id
        model.description = receivable.description
        model.total_amount_cents = receivable.total_amount_cents
        model.status = receivable.status
        model.issue_date = receivable.issue_date
        model.due_date = receivable.due_date
        model.received_at = receivable.received_at
        model.received_amount_cents = receivable.received_amount_cents
        model.source_type = receivable.source_type
        model.source_id = receivable.source_id
        self._session.add(model)
        self._session.flush()
        receivable.id = model.id

    def get_by_id(self, receivable_id: int) -> Receivable | None:
        model = self._session.get(ReceivableModel, receivable_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(
        self, company_id: int | None = None, status: str | None = None
    ) -> list[Receivable]:
        stmt = select(ReceivableModel)
        if company_id is not None:
            stmt = stmt.where(ReceivableModel.company_id == company_id)
        if status is not None:
            stmt = stmt.where(ReceivableModel.status == status)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def save(self, receivable: Receivable) -> None:
        model = self._session.get(ReceivableModel, receivable.id)
        if model is None:
            raise ValueError(f"Receivable {receivable.id} not found")
        model.customer_id = receivable.customer_id
        model.category_id = receivable.category_id
        model.description = receivable.description
        model.total_amount_cents = receivable.total_amount_cents
        model.status = receivable.status
        model.due_date = receivable.due_date
        model.received_at = receivable.received_at
        model.received_amount_cents = receivable.received_amount_cents
        model.source_type = receivable.source_type
        model.source_id = receivable.source_id
        self._session.flush()

    def _model_to_domain(self, model: ReceivableModel) -> Receivable:
        return Receivable(
            id=model.id,
            company_id=model.company_id,
            customer_id=model.customer_id,
            category_id=model.category_id,
            description=model.description,
            total_amount_cents=model.total_amount_cents,
            status=model.status,
            issue_date=model.issue_date,
            due_date=model.due_date,
            received_at=model.received_at,
            received_amount_cents=model.received_amount_cents,
            source_type=model.source_type,
            source_id=model.source_id,
        )
