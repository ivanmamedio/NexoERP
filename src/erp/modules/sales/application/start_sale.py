"""Start sale use case."""

from __future__ import annotations

from erp.modules.sales.application.ports import SaleRepository
from erp.modules.sales.domain.sale import Sale


class StartSaleInput:
    def __init__(
        self,
        *,
        user_id: int | None,
        username: str,
        session_id: int | None = None,
        company_id: int | None = None,
    ) -> None:
        self.user_id = user_id
        self.username = username
        self.session_id = session_id
        self.company_id = company_id


class StartSaleOutput:
    def __init__(self, sale: Sale) -> None:
        self.sale = sale


class StartSale:
    def __init__(self, repository: SaleRepository) -> None:
        self._repository = repository

    def execute(self, input: StartSaleInput) -> StartSaleOutput:
        sale = Sale(
            user_id=input.user_id,
            username=input.username,
            session_id=input.session_id,
            company_id=input.company_id,
        )
        self._repository.add(sale)
        return StartSaleOutput(sale=sale)
