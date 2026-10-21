"""SQLAlchemy repositories for the purchases module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select

from erp.modules.purchases.application.ports import (
    PurchaseItemRepository,
    PurchaseRepository,
)
from erp.modules.purchases.domain.purchase import Purchase, PurchaseItem
from erp.modules.purchases.infrastructure.models import (
    PurchaseItemModel,
    PurchaseModel,
)
from erp.shared.infrastructure.repository import SqlAlchemyRepository


class SqlAlchemyPurchaseRepository(
    SqlAlchemyRepository[PurchaseModel, Purchase, int], PurchaseRepository
):
    """SQLAlchemy implementation of PurchaseRepository."""

    _model_cls = PurchaseModel

    def _to_domain(self, model: PurchaseModel) -> Purchase:
        return Purchase(
            id=model.id,
            company_id=model.company_id or 0,
            supplier_id=model.supplier_id,
            user_id=model.user_id,
            username=model.username,
            purchase_date=model.purchase_date,
            total_cents=model.total_cents,
            status=model.status,
        )

    def _to_model(self, domain: Purchase) -> PurchaseModel:
        model = PurchaseModel()
        model.company_id = domain.company_id
        model.supplier_id = domain.supplier_id
        model.user_id = domain.user_id
        model.username = domain.username
        model.purchase_date = domain.purchase_date or datetime.now(UTC)
        model.total_cents = domain.total_cents
        model.status = domain.status
        return model

    def list_by_company(self, company_id: int) -> list[Purchase]:
        stmt = (
            select(PurchaseModel)
            .where(PurchaseModel.company_id == company_id)
            .order_by(PurchaseModel.purchase_date.desc())
        )
        models = self._session.execute(stmt).scalars().all()
        return cast(list[Purchase], [self._to_domain(m) for m in models])


class SqlAlchemyPurchaseItemRepository(
    SqlAlchemyRepository[PurchaseItemModel, PurchaseItem, int], PurchaseItemRepository
):
    """SQLAlchemy implementation of PurchaseItemRepository."""

    _model_cls = PurchaseItemModel

    def _to_domain(self, model: PurchaseItemModel) -> PurchaseItem:
        return PurchaseItem(
            id=model.id,
            purchase_id=model.purchase_id,
            product_id=model.product_id,
            quantity_thousandths=model.quantity_thousandths,
            unit_cost_cents=model.unit_cost_cents,
            line_total_cents=model.line_total_cents,
        )

    def _to_model(self, domain: PurchaseItem) -> PurchaseItemModel:
        model = PurchaseItemModel()
        model.purchase_id = domain.purchase_id
        model.product_id = domain.product_id
        model.quantity_thousandths = domain.quantity_thousandths
        model.unit_cost_cents = domain.unit_cost_cents
        model.line_total_cents = domain.line_total_cents
        return model

    def list_by_purchase(self, purchase_id: int) -> list[PurchaseItem]:
        stmt = select(PurchaseItemModel).where(PurchaseItemModel.purchase_id == purchase_id)
        models = self._session.execute(stmt).scalars().all()
        return cast(list[PurchaseItem], [self._to_domain(m) for m in models])
