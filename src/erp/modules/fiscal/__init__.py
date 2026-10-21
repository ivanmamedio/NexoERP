"""Fiscal module - interface for fiscal document emission adapters."""

from erp.modules.fiscal.application import (
    FiscalPort,
    FiscalService,
    create_fiscal_service,
)
from erp.modules.fiscal.domain import (
    FiscalDocument,
    FiscalDocumentStatus,
    FiscalDocumentType,
    FiscalOperationResult,
)
from erp.modules.fiscal.infrastructure import NoOpFiscalAdapter

__all__ = [
    "FiscalDocument",
    "FiscalDocumentStatus",
    "FiscalDocumentType",
    "FiscalOperationResult",
    "FiscalPort",
    "FiscalService",
    "NoOpFiscalAdapter",
    "create_fiscal_service",
]
