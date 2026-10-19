"""SQLAlchemy repository for treasury financial entries."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.treasury.application.ports import FinancialEntryRepository
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.infrastructure.models import FinancialEntryModel


class SqlAlchemyFinancialEntryRepository(FinancialEntryRepository):
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

    def list_by_company(
        self, company_id: int | None = None
    ) -> list[FinancialEntry]:
        stmt = select(FinancialEntryModel)
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
