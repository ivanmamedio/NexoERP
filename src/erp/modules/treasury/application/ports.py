"""Application ports for the treasury module."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from erp.modules.treasury.domain.financial_category import FinancialCategory
from erp.modules.treasury.domain.financial_entry import FinancialEntry
from erp.modules.treasury.domain.payable import Payable
from erp.modules.treasury.domain.receivable import Receivable


@runtime_checkable
class FinancialEntryRepository(Protocol):
    def add(self, entry: FinancialEntry) -> None: ...
    def list_by_company(self, company_id: int | None = None) -> list[FinancialEntry]: ...
    def list_by_period(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
    ) -> list[FinancialEntry]: ...


@runtime_checkable
class FinancialCategoryRepository(Protocol):
    def add(self, category: FinancialCategory) -> None: ...
    def get_by_id(self, category_id: int) -> FinancialCategory | None: ...
    def get_by_name(self, name: str, company_id: int | None = None) -> FinancialCategory | None: ...
    def list_all(self, company_id: int | None = None) -> list[FinancialCategory]: ...
    def save(self, category: FinancialCategory) -> None: ...
    def delete(self, category_id: int) -> None: ...


@runtime_checkable
class PayableRepository(Protocol):
    def add(self, payable: Payable) -> None: ...
    def get_by_id(self, payable_id: int) -> Payable | None: ...
    def list_by_company(
        self, company_id: int | None = None, status: str | None = None
    ) -> list[Payable]: ...
    def list_by_due_date_range(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
        status: str | None = None,
    ) -> list[Payable]: ...
    def save(self, payable: Payable) -> None: ...


@runtime_checkable
class ReceivableRepository(Protocol):
    def add(self, receivable: Receivable) -> None: ...
    def get_by_id(self, receivable_id: int) -> Receivable | None: ...
    def list_by_company(
        self, company_id: int | None = None, status: str | None = None
    ) -> list[Receivable]: ...
    def list_by_due_date_range(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        company_id: int | None = None,
        status: str | None = None,
    ) -> list[Receivable]: ...
    def save(self, receivable: Receivable) -> None: ...
