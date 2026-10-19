"""Application ports for the treasury module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.treasury.domain.financial_entry import FinancialEntry


@runtime_checkable
class FinancialEntryRepository(Protocol):
    def add(self, entry: FinancialEntry) -> None: ...
    def list_by_company(
        self, company_id: int | None = None
    ) -> list[FinancialEntry]: ...
