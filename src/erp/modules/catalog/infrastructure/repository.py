"""SQLAlchemy repositories for the catalog module."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from erp.modules.catalog.application.ports import (
    ProductRepository,
    StockMovementRepository,
)
from erp.modules.catalog.domain.category import Category
from erp.modules.catalog.domain.product import Product
from erp.modules.catalog.domain.stock_movement import StockMovement
from erp.modules.catalog.domain.supplier import Supplier
from erp.modules.catalog.infrastructure.models import (
    CategoryModel,
    ProductModel,
    StockMovementModel,
    SupplierModel,
)
from erp.shared.application.session import CurrentSession


class SqlAlchemyProductRepository(ProductRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _company_id(self) -> int | None:
        return CurrentSession().company_id

    def _filter_company(self, stmt: select) -> select:  # type: ignore[valid-type]
        company_id = self._company_id()
        if company_id is not None:
            stmt = stmt.where(ProductModel.company_id == company_id)  # type: ignore[attr-defined]
        return stmt

    def add(self, product: Product) -> None:
        model = ProductModel()
        model.company_id = product.company_id or self._company_id()
        if model.company_id is None:
            raise ValueError("Product must have a company_id or an active company session")
        model.sku = product.sku
        model.name = product.name
        model.description = product.description
        model.category_id = product.category_id
        model.supplier_id = product.supplier_id
        model.unit = product.unit
        model.cost_cents = product.cost_cents
        model.margin_pct = product.margin_pct
        model.price_cents = product.price_cents
        model.min_stock_qty = product.min_stock_qty
        model.stock_qty = product.stock_qty
        model.sold_by_weight = product.sold_by_weight
        model.active = product.active
        self._session.add(model)
        self._session.flush()
        product.id = model.id

    def save(self, product: Product) -> None:
        if product.id is None:
            raise ValueError("Product must have an id to update")
        model = self._session.get(ProductModel, product.id)
        if model is None:
            raise ValueError(f"Product {product.id} not found")
        model.sku = product.sku
        model.name = product.name
        model.description = product.description
        model.category_id = product.category_id
        model.supplier_id = product.supplier_id
        model.unit = product.unit
        model.cost_cents = product.cost_cents
        model.margin_pct = product.margin_pct
        model.price_cents = product.price_cents
        model.min_stock_qty = product.min_stock_qty
        model.stock_qty = product.stock_qty
        model.sold_by_weight = product.sold_by_weight
        model.active = product.active
        self._session.add(model)
        self._session.flush()

    def get_by_id(self, product_id: int) -> Product | None:
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        model = self._session.execute(self._filter_company(stmt)).scalar_one_or_none()  # type: ignore[misc]
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None:
        stmt = select(ProductModel).where(ProductModel.sku == sku)
        if company_id is not None:
            stmt = stmt.where(ProductModel.company_id == company_id)
        else:
            stmt = self._filter_company(stmt)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, company_id: int | None = None) -> list[Product]:
        stmt = select(ProductModel)
        if company_id is not None:
            stmt = stmt.where(ProductModel.company_id == company_id)
        else:
            stmt = self._filter_company(stmt)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    def list_all_skus(self, company_id: int | None = None) -> list[str]:
        """Lista todos os SKUs de produtos para uma empresa."""
        stmt = select(ProductModel.sku)
        if company_id is not None:
            stmt = stmt.where(ProductModel.company_id == company_id)
        else:
            stmt = self._filter_company(stmt)
        models = self._session.execute(stmt).scalars().all()
        return list(models)

    def add_snapshot(self, product_snapshot: object) -> None:
        """Adiciona um produto via snapshot (port do import_csv)."""
        model = ProductModel()
        model.company_id = product_snapshot.company_id  # type: ignore[attr-defined]
        model.sku = product_snapshot.sku  # type: ignore[attr-defined]
        model.name = product_snapshot.name  # type: ignore[attr-defined]
        model.description = product_snapshot.description  # type: ignore[attr-defined]
        model.unit = product_snapshot.unit  # type: ignore[attr-defined]
        model.cost_cents = product_snapshot.cost_cents  # type: ignore[attr-defined]
        model.margin_pct = product_snapshot.margin_pct  # type: ignore[attr-defined]
        model.price_cents = product_snapshot.price_cents  # type: ignore[attr-defined]
        model.min_stock_qty = product_snapshot.min_stock_qty  # type: ignore[attr-defined]
        model.stock_qty = product_snapshot.stock_qty  # type: ignore[attr-defined]
        model.sold_by_weight = product_snapshot.sold_by_weight  # type: ignore[attr-defined]
        model.active = product_snapshot.active  # type: ignore[attr-defined]
        self._session.add(model)
        self._session.flush()

    def commit(self) -> None:
        """Confirma a transação atual."""
        self._session.commit()

    def _active_products(self, company_id: int | None) -> Select[ProductModel]:
        stmt: Select[ProductModel] = select(ProductModel).where(ProductModel.active.is_(True))
        cid = company_id if company_id is not None else self._company_id()
        if cid is not None:
            stmt = stmt.where(ProductModel.company_id == cid)
        return stmt

    def search(self, query: str, company_id: int | None = None, limit: int = 20) -> list[Product]:
        """Busca produtos ativos por nome.

        Tenta primeiro o prefixo (aproveita o índice NOCASE); se não houver
        resultado, cai para substring. Wildcards de LIKE são escapados.
        """
        term = query.strip()
        if not term or limit <= 0:
            return []
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        prefix_stmt = (
            self._active_products(company_id)
            .where(ProductModel.name.like(f"{escaped}%", escape="\\"))
            .order_by(ProductModel.name)
            .limit(limit)
        )
        models = list(self._session.execute(prefix_stmt).scalars().all())
        if not models:
            contains_stmt = (
                self._active_products(company_id)
                .where(ProductModel.name.like(f"%{escaped}%", escape="\\"))
                .order_by(ProductModel.name)
                .limit(limit)
            )
            models = list(self._session.execute(contains_stmt).scalars().all())
        return [self._model_to_domain(m) for m in models]

    def delete(self, product_id: int) -> None:
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        model = self._session.execute(self._filter_company(stmt)).scalar_one_or_none()  # type: ignore[misc]
        if model is None:
            raise ValueError(f"Product {product_id} not found")
        self._session.delete(model)

    @staticmethod
    def _model_to_domain(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            company_id=model.company_id,
            sku=model.sku,
            name=model.name,
            description=model.description,
            category_id=model.category_id,
            supplier_id=model.supplier_id,
            unit=model.unit,
            cost_cents=model.cost_cents,
            margin_pct=model.margin_pct,
            price_cents=model.price_cents,
            min_stock_qty=model.min_stock_qty,
            stock_qty=model.stock_qty,
            sold_by_weight=model.sold_by_weight,
            active=model.active,
        )


class SqlAlchemyCategoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, category: Category) -> None:
        model = CategoryModel()
        model.company_id = category.company_id or CurrentSession().company_id
        model.name = category.name
        model.description = category.description
        model.parent_id = category.parent_id
        model.is_active = category.is_active
        self._session.add(model)
        self._session.flush()
        category.id = model.id

    def get_by_id(self, category_id: int) -> Category | None:
        model = self._session.get(CategoryModel, category_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, company_id: int | None = None) -> list[Category]:
        stmt = select(CategoryModel)
        if company_id is not None:
            stmt = stmt.where(CategoryModel.company_id == company_id)
        else:
            cid = CurrentSession().company_id
            if cid is not None:
                stmt = stmt.where(CategoryModel.company_id == cid)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            description=model.description,
            parent_id=model.parent_id,
            is_active=model.is_active,
        )


class SqlAlchemySupplierRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, supplier: Supplier) -> None:
        model = SupplierModel()
        model.company_id = supplier.company_id or CurrentSession().company_id
        model.name = supplier.name
        model.trade_name = supplier.trade_name
        model.tax_id = supplier.tax_id
        model.contact_name = supplier.contact_name
        model.phone = supplier.phone
        model.email = supplier.email
        model.address = supplier.address
        model.is_active = supplier.is_active
        self._session.add(model)
        self._session.flush()
        supplier.id = model.id

    def get_by_id(self, supplier_id: int) -> Supplier | None:
        model = self._session.get(SupplierModel, supplier_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_all(self, company_id: int | None = None) -> list[Supplier]:
        stmt = select(SupplierModel)
        if company_id is not None:
            stmt = stmt.where(SupplierModel.company_id == company_id)
        else:
            cid = CurrentSession().company_id
            if cid is not None:
                stmt = stmt.where(SupplierModel.company_id == cid)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: SupplierModel) -> Supplier:
        return Supplier(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            trade_name=model.trade_name,
            tax_id=model.tax_id,
            contact_name=model.contact_name,
            phone=model.phone,
            email=model.email,
            address=model.address,
            is_active=model.is_active,
        )


class SqlAlchemyStockMovementRepository(StockMovementRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, movement: StockMovement) -> None:
        model = StockMovementModel()
        model.product_id = movement.product_id
        model.company_id = movement.company_id
        model.quantity_thousandths = movement.quantity_thousandths
        model.movement_type = movement.movement_type
        model.reference_id = movement.reference_id
        model.notes = movement.notes
        model.created_at = movement.created_at  # type: ignore[assignment]
        model.user_id = movement.user_id
        model.username = movement.username
        self._session.add(model)
        self._session.flush()
        movement.id = model.id

    def list_by_product(self, product_id: int) -> list[StockMovement]:
        stmt = select(StockMovementModel).where(StockMovementModel.product_id == product_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: StockMovementModel) -> StockMovement:
        return StockMovement(
            id=model.id,
            product_id=model.product_id,
            company_id=model.company_id,
            quantity_thousandths=model.quantity_thousandths,
            movement_type=model.movement_type,
            reference_id=model.reference_id,
            notes=model.notes,
            created_at=model.created_at,
            user_id=model.user_id,
            username=model.username,
        )
