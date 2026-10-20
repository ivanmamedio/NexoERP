"""No-op fiscal adapter for testing and development."""

from __future__ import annotations

from erp.modules.fiscal.application.ports import FiscalPort
from erp.modules.fiscal.domain import (
    FiscalDocument,
    FiscalDocumentType,
    FiscalOperationResult,
)


class NoOpFiscalAdapter(FiscalPort):
    """No-op fiscal adapter that simulates successful operations.

    This adapter is used for testing and development environments
    where no real fiscal provider is configured.
    """

    def emit_document(self, document: FiscalDocument) -> FiscalOperationResult:
        """Simulate successful document emission."""
        return FiscalOperationResult.success_result(
            document_id=f"noop-{document.document_type.value}-{document.company_id}-{document.series}-{document.number}",
            protocol="NOOP-PROTOCOL",
            xml_content=f"<xml>Simulated {document.document_type.value}</xml>",
        )

    def cancel_document(
        self, document_id: str, justification: str
    ) -> FiscalOperationResult:
        """Simulate successful document cancellation."""
        return FiscalOperationResult.success_result(
            document_id=document_id,
            protocol="NOOP-CANCEL-PROTOCOL",
        )

    def consult_document(self, document_id: str) -> FiscalOperationResult:
        """Simulate document consultation."""
        return FiscalOperationResult.success_result(
            document_id=document_id,
            protocol="NOOP-CONSULT-PROTOCOL",
            xml_content=f"<xml>Status for {document_id}</xml>",
        )

    def get_supported_types(self) -> list[FiscalDocumentType]:
        """Return all supported document types."""
        return list(FiscalDocumentType)