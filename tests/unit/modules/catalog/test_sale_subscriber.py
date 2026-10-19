"""Unit tests for CatalogSaleSubscriber."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from erp.modules.catalog.application.sale_subscriber import CatalogSaleSubscriber
from erp.modules.catalog.infrastructure.models import (
    Base,
    ProductModel,
    StockMovementModel,
)
from erp.modules.sales.infrastructure.models import SaleItemModel, SaleModel
from erp.shared.application.events import EventBus
from erp.shared.domain.events import SaleCompleted


def _create_tables(session: Session) -> None:
    Base.metadata.create_all(session.get_bind())


def _insert_product(session: Session, product_id: int, stock_qty: int) -> None:
    session.execute(
        ProductModel.__table__.insert(),
        [
            {
                "id": product_id,
                "company_id": 1,
                "sku": "ARROZ-5KG",
                "name": "Arroz 5kg",
                "unit": "un",
                "price_cents": 2500,
                "stock_qty": stock_qty,
                "active": True,
            }
        ],
    )


def _insert_sale(session: Session, sale_id: int) -> int:
    result = session.execute(
        SaleModel.__table__.insert(),
        [
            {
                "id": sale_id,
                "company_id": 1,
                "status": "finalized",
                "subtotal_cents": 5000,
                "discount_cents": 0,
                "total_cents": 5000,
                "paid_cents": 5000,
                "change_cents": 0,
                "username": "caixa",
                "created_at": datetime.now(UTC),
            }
        ],
    )
    return result.inserted_primary_key[0]


def _insert_sale_item(
    session: Session, item_id: int, sale_id: int, product_id: int, qty: int, price: int
) -> None:
    session.execute(
        SaleItemModel.__table__.insert(),
        [
            {
                "id": item_id,
                "sale_id": sale_id,
                "company_id": 1,
                "product_id": product_id,
                "description": "Arroz 5kg",
                "unit_price_cents": price,
                "quantity_thousandths": qty,
                "line_total_cents": price * qty // 1000,
                "unit": "un",
                "cancelled": False,
            }
        ],
    )


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_catalog_sale_subscriber_creates_stock_movements(engine) -> None:
    with Session(engine) as session:
        _insert_product(session, 1, 100000)
        sale_id = _insert_sale(session, 1)
        _insert_sale_item(session, 1, sale_id, 1, 2000, 2500)
        _insert_sale_item(session, 2, sale_id, 1, 3000, 2500)
        session.commit()

    event_bus = EventBus()
    CatalogSaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=sale_id,
        company_id=1,
        session_id=None,
        user_id=1,
        username="caixa",
        total_cents=5000,
        cash_cents=5000,
        pix_cents=0,
        card_cents=0,
        items=[
            {"product_id": 1, "quantity_thousandths": 2000},
            {"product_id": 1, "quantity_thousandths": 3000},
        ],
    )
    event_bus.publish(event)

    with Session(engine) as session:
        movements = (
            session.query(StockMovementModel)
            .filter_by(reference_id=sale_id)
            .order_by(StockMovementModel.id)
            .all()
        )
        assert len(movements) == 2
        # Both are sales (negative quantity)
        assert movements[0].quantity_thousandths == -2000
        assert movements[0].movement_type == "sale"
        assert movements[1].quantity_thousandths == -3000
        assert movements[1].movement_type == "sale"


def test_catalog_sale_subscriber_skips_cancelled_items(engine) -> None:
    with Session(engine) as session:
        _insert_product(session, 1, 100000)
        sale_id = _insert_sale(session, 1)
        _insert_sale_item(session, 1, sale_id, 1, 2000, 2500)
        # Mark second item as cancelled
        session.execute(
            SaleItemModel.__table__.insert(),
            [
                {
                    "id": 2,
                    "sale_id": sale_id,
                    "company_id": 1,
                    "product_id": 1,
                    "description": "Arroz 5kg",
                    "unit_price_cents": 2500,
                    "quantity_thousandths": 3000,
                    "line_total_cents": 7500,
                    "unit": "un",
                    "cancelled": True,
                }
            ],
        )
        session.commit()

    event_bus = EventBus()
    CatalogSaleSubscriber(event_bus=event_bus, engine=engine)

    event = SaleCompleted(
        sale_id=sale_id,
        company_id=1,
        session_id=None,
        user_id=1,
        username="caixa",
        total_cents=5000,
        cash_cents=5000,
        pix_cents=0,
        card_cents=0,
        items=[
            {"product_id": 1, "quantity_thousandths": 2000},
        ],
    )
    event_bus.publish(event)

    with Session(engine) as session:
        movements = (
            session.query(StockMovementModel)
            .filter_by(reference_id=sale_id)
            .all()
        )
        assert len(movements) == 1  # Only the non-cancelled item
        assert movements[0].quantity_thousandths == -2000
