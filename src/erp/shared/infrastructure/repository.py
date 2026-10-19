"""Generic SQLAlchemy repository base class.

Eliminates boilerplate in module-specific repositories.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar, cast

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from erp.shared.application.session import CurrentSession
from erp.shared.domain.entities import Entity

if TYPE_CHECKING:
    pass

Model = TypeVar("Model")
Domain = TypeVar("Domain", bound=Entity)
ID = TypeVar("ID", int, str)


class HasId:
    """Protocol for models with an 'id' column."""

    id: int


class SqlAlchemyRepository[Model, Domain: Entity, ID: (int, str)]:
    """Generic repository with common CRUD + company filtering.

    Subclasses must implement:
        - _model_cls: the SQLAlchemy model class
        - _to_domain(model: Model) -> Domain
        - _to_model(domain: Domain) -> Model
        - _company_id_column: str name of company_id column (optional)

    Optional overrides:
        - _get_by_id_stmt(id) -> Select: custom lookup (e.g., by SKU)
        - _apply_company_filter(stmt) -> Select: custom filter logic
    """

    _model_cls: type[Model]
    _company_id_column: str | None = None  # e.g., "company_id"

    def __init__(self, session: Session) -> None:
        self._session = session

    # =========================================================================
    # Abstract methods (must be implemented by subclasses)
    # =========================================================================

    def _to_domain(self, model: Model) -> Domain:
        raise NotImplementedError

    def _to_model(self, domain: Domain) -> Model:
        raise NotImplementedError

    # =========================================================================
    # Company filtering (cross-cutting concern)
    # =========================================================================

    def _company_id(self) -> int | None:
        """Get company_id from current session (thread-local)."""
        return CurrentSession().company_id

    def _apply_company_filter(self, stmt: Select[Any]) -> Select[Any]:
        """Apply company_id filter if column exists and session has company."""
        company_id = self._company_id()
        if company_id is not None and self._company_id_column is not None:
            column = getattr(self._model_cls, self._company_id_column)
            from sqlalchemy import ColumnElement
            stmt = stmt.where(cast("ColumnElement[bool]", column == company_id))
        return stmt

    # =========================================================================
    # CRUD operations (implemented generically)
    # =========================================================================

    def add(self, domain: Domain) -> None:
        """Persist new entity. Sets company_id from session if not provided."""
        model = self._to_model(domain)
        if self._company_id_column is not None:
            current_value = getattr(model, self._company_id_column, None)
            if current_value is None:
                company_id = self._company_id()
                if company_id is not None:
                    setattr(model, self._company_id_column, company_id)
        self._session.add(model)
        self._session.flush()
        # Update domain ID if auto-generated and domain has id attribute
        if hasattr(model, "id") and hasattr(domain, "id") and getattr(domain, "id", None) is None:
            domain.id = model.id

    def save(self, domain: Domain) -> None:
        """Update existing entity. Requires domain.id to be set."""
        if domain.id is None:
            raise ValueError(f"{self._model_cls.__name__} must have an id to update")
        model = self._session.get(self._model_cls, domain.id)
        if model is None:
            raise ValueError(f"{self._model_cls.__name__} {domain.id} not found")
        # Copy all fields from domain to model
        self._copy_domain_to_model(domain, model)
        self._session.add(model)
        self._session.flush()

    def _copy_domain_to_model(self, domain: Domain, model: Model) -> None:
        """Copy domain fields to model. Override for complex mappings."""
        for key in domain.__dataclass_fields__:
            if key == "id":
                continue
            value = getattr(domain, key)
            if hasattr(model, key):
                setattr(model, key, value)

    def get_by_id(self, id: ID) -> Domain | None:
        """Find by primary key, applying company filter."""
        stmt = select(self._model_cls).where(self._model_cls.id == id)  # type: ignore[attr-defined]
        stmt = self._apply_company_filter(stmt)
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def delete(self, id: ID) -> None:
        """Delete by primary key, applying company filter."""
        domain = self.get_by_id(id)
        if domain is None:
            return
        stmt = select(self._model_cls).where(self._model_cls.id == id)  # type: ignore[attr-defined]
        stmt = self._apply_company_filter(stmt)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model:
            self._session.delete(model)
            self._session.flush()

    def list_all(self, *, company_id: int | None = None) -> Sequence[Domain]:
        """List all entities, optionally filtering by company."""
        stmt = select(self._model_cls)
        if company_id is not None and self._company_id_column is not None:
            column = getattr(self._model_cls, self._company_id_column)
            stmt = stmt.where(column == company_id)
        elif self._company_id_column is not None:
            stmt = self._apply_company_filter(stmt)
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]