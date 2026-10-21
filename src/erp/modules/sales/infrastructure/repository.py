"""SQLAlchemy repositories for the sales module."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.sales.application.ports import (
    SaleItemRepository,
    SalePaymentRepository,
    SaleRepository,
)
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.modules.sales.domain.sale_payment import SalePayment
from erp.modules.sales.infrastructure.models import (
    SaleItemModel,
    SaleModel,
    SalePaymentModel,
)
from erp.shared.application.session import CurrentSession


class SqlAlchemySaleRepository(SaleRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, sale: Sale) -> None:
        model = SaleModel()
        model.company_id = sale.company_id or CurrentSession().company_id
        model.session_id = sale.session_id
        model.user_id = sale.user_id
        model.username = sale.username
        model.status = sale.status
        model.subtotal_cents = sale.subtotal_cents
        model.discount_cents = sale.discount_cents
        model.total_cents = sale.total_cents
        model.paid_cents = sale.paid_cents
        model.change_cents = sale.change_cents
        model.cancel_reason = sale.cancel_reason
        model.cancelled_by_user_id = sale.cancelled_by_user_id
        model.cancelled_by_username = sale.cancelled_by_username
        model.authorized_by_user_id = sale.authorized_by_user_id
        model.authorized_by_username = sale.authorized_by_username
        model.created_at = sale.created_at  # type: ignore[assignment]
        model.finalized_at = sale.finalized_at
        model.cancelled_at = sale.cancelled_at
        self._session.add(model)
        self._session.flush()
        sale.id = model.id

    def save(self, sale: Sale) -> None:
        if sale.id is None:
            raise ValueError("Sale must have an id to update")
        model = self._session.get(SaleModel, sale.id)
        if model is None:
            raise ValueError(f"Sale {sale.id} not found")
        model.status = sale.status
        model.subtotal_cents = sale.subtotal_cents
        model.discount_cents = sale.discount_cents
        model.total_cents = sale.total_cents
        model.paid_cents = sale.paid_cents
        model.change_cents = sale.change_cents
        model.session_id = sale.session_id
        model.cancel_reason = sale.cancel_reason
        model.cancelled_by_user_id = sale.cancelled_by_user_id
        model.cancelled_by_username = sale.cancelled_by_username
        model.authorized_by_user_id = sale.authorized_by_user_id
        model.authorized_by_username = sale.authorized_by_username
        model.finalized_at = sale.finalized_at
        model.cancelled_at = sale.cancelled_at
        self._session.add(model)
        self._session.flush()

    def get_by_id(self, sale_id: int, company_id: int | None = None) -> Sale | None:
        stmt = select(SaleModel).where(SaleModel.id == sale_id)
        if company_id is not None:
            stmt = stmt.where(SaleModel.company_id == company_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_open(self, company_id: int | None = None) -> list[Sale]:
        stmt = select(SaleModel).where(SaleModel.status == "draft")
        cid = company_id if company_id is not None else CurrentSession().company_id
        if cid is not None:
            stmt = stmt.where(SaleModel.company_id == cid)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: SaleModel) -> Sale:
        return Sale(
            id=model.id,
            company_id=model.company_id,
            session_id=model.session_id,
            user_id=model.user_id,
            username=model.username,
            status=model.status,
            subtotal_cents=model.subtotal_cents,
            discount_cents=model.discount_cents,
            total_cents=model.total_cents,
            paid_cents=model.paid_cents,
            change_cents=model.change_cents,
            cancel_reason=model.cancel_reason,
            cancelled_by_user_id=model.cancelled_by_user_id,
            cancelled_by_username=model.cancelled_by_username,
            authorized_by_user_id=model.authorized_by_user_id,
            authorized_by_username=model.authorized_by_username,
            created_at=model.created_at,
            finalized_at=model.finalized_at,
            cancelled_at=model.cancelled_at,
        )


class SqlAlchemySaleItemRepository(SaleItemRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, item: SaleItem) -> None:
        model = SaleItemModel()
        model.sale_id = item.sale_id
        model.company_id = item.company_id
        model.product_id = item.product_id
        model.description = item.description
        model.unit_price_cents = item.unit_price_cents
        model.quantity_thousandths = item.quantity_thousandths
        model.line_total_cents = item.line_total_cents
        model.unit = item.unit
        model.cancelled = item.cancelled
        model.cancel_reason = item.cancel_reason
        self._session.add(model)
        self._session.flush()
        item.id = model.id

    def save(self, item: SaleItem) -> None:
        if item.id is None:
            raise ValueError("Item must have an id to update")
        model = self._session.get(SaleItemModel, item.id)
        if model is None:
            raise ValueError(f"Item {item.id} not found")
        model.unit_price_cents = item.unit_price_cents
        model.quantity_thousandths = item.quantity_thousandths
        model.line_total_cents = item.line_total_cents
        model.cancelled = item.cancelled
        model.cancel_reason = item.cancel_reason
        self._session.add(model)
        self._session.flush()

    def get_by_id(self, item_id: int) -> SaleItem | None:
        model = self._session.get(SaleItemModel, item_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_sale(self, sale_id: int) -> list[SaleItem]:
        stmt = select(SaleItemModel).where(SaleItemModel.sale_id == sale_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: SaleItemModel) -> SaleItem:
        return SaleItem(
            id=model.id,
            sale_id=model.sale_id,
            company_id=model.company_id,
            product_id=model.product_id,
            description=model.description,
            unit_price_cents=model.unit_price_cents,
            quantity_thousandths=model.quantity_thousandths,
            line_total_cents=model.line_total_cents,
            unit=model.unit,
            cancelled=model.cancelled,
            cancel_reason=model.cancel_reason,
        )


class SqlAlchemySalePaymentRepository(SalePaymentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, payment: SalePayment) -> None:
        model = SalePaymentModel()
        model.sale_id = payment.sale_id
        model.company_id = payment.company_id
        model.method = payment.method
        model.amount_cents = payment.amount_cents
        model.change_cents = payment.change_cents
        self._session.add(model)
        self._session.flush()
        payment.id = model.id

    def list_by_sale(self, sale_id: int) -> list[SalePayment]:
        stmt = select(SalePaymentModel).where(SalePaymentModel.sale_id == sale_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: SalePaymentModel) -> SalePayment:
        return SalePayment(
            id=model.id,
            sale_id=model.sale_id,
            company_id=model.company_id,
            method=model.method,
            amount_cents=model.amount_cents,
            change_cents=model.change_cents,
        )
