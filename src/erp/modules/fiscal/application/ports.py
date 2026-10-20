"""Fiscal module - interface for fiscal adapters."""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from erp.modules.fiscal.domain import FiscalDocument, FiscalDocumentType, FiscalOperationResult


@runtime_checkable
class FiscalPort(Protocol):
    """Protocol for fiscal document emission adapters.

    This interface allows the sales flow to work with any fiscal provider
    (NFe, NFCe, SAT, etc.) without depending on a specific implementation.
    """

    @abstractmethod
    def emit_document(
        self,
        document: FiscalDocument,
    ) -> FiscalOperationResult:
        """Emit a fiscal document.

        Args:
            document: The fiscal document to emit.

        Returns:
            Result of the emission operation.
        """
        ...

    @abstractmethod
    def cancel_document(
        self,
        document_id: str,
        justification: str,
    ) -> FiscalOperationResult:
        """Cancel a previously emitted fiscal document.

        Args:
            document_id: The ID of the document to cancel.
            justification: Reason for cancellation.

        Returns:
            Result of the cancellation operation.
        """
        ...

    @abstractmethod
    def consult_document(
        self,
        document_id: str,
    ) -> FiscalOperationResult:
        """Consult the status of a fiscal document.

        Args:
            document_id: The ID of the document to consult.

        Returns:
            Result with the document status.
        """
        ...

    @abstractmethod
    def get_supported_types(self) -> list[FiscalDocumentType]:
        """Get the list of supported document types.

        Returns:
            List of supported fiscal document types.
        """
        ...