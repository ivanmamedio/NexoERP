"""Fiscal service for document emission."""

from __future__ import annotations

from erp.modules.fiscal.application.ports import FiscalPort
from erp.modules.fiscal.domain import (
    FiscalDocument,
    FiscalDocumentType,
    FiscalOperationResult,
)


class FiscalService:
    """Service for fiscal document operations."""

    def __init__(self, adapter: FiscalPort | None = None) -> None:
        self._adapter = adapter

    @property
    def adapter(self) -> FiscalPort | None:
        return self._adapter

    def set_adapter(self, adapter: FiscalPort) -> None:
        self._adapter = adapter

    def is_configured(self) -> bool:
        return self._adapter is not None

    def emit_document(self, document: FiscalDocument) -> FiscalOperationResult:
        if self._adapter is None:
            return FiscalOperationResult.error_result(
                error_code="NO_ADAPTER",
                error_message="Nenhum adaptador fiscal configurado",
                document_id="",
            )
        return self._adapter.emit_document(document)

    def cancel_document(
        self, document_id: str, justification: str
    ) -> FiscalOperationResult:
        if self._adapter is None:
            return FiscalOperationResult.error_result(
                error_code="NO_ADAPTER",
                error_message="Nenhum adaptador fiscal configurado",
                document_id=document_id,
            )
        return self._adapter.cancel_document(document_id, justification)

    def consult_document(self, document_id: str) -> FiscalOperationResult:
        if self._adapter is None:
            return FiscalOperationResult.error_result(
                error_code="NO_ADAPTER",
                error_message="Nenhum adaptador fiscal configurado",
                document_id=document_id,
            )
        return self._adapter.consult_document(document_id)

    def get_supported_types(self) -> list[FiscalDocumentType]:
        if self._adapter is None:
            return []
        return self._adapter.get_supported_types()


def create_fiscal_service(adapter: FiscalPort | None = None) -> FiscalService:
    return FiscalService(adapter)