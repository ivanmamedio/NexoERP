"""Fiscal domain entities and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


class FiscalDocumentType(StrEnum):
    """Types of fiscal documents."""

    NFE = "nfe"  # Nota Fiscal Eletrônica
    NFCE = "nfce"  # Nota Fiscal de Consumidor Eletrônica
    SAT = "sat"  # Sistema Autenticador e Transmissor
    CTE = "cte"  # Conhecimento de Transporte Eletrônico
    MDFE = "mdfe"  # Manifesto Eletrônico de Documentos Fiscais
    CFE = "cfe"  # Cupom Fiscal Eletrônico (SAT)


class FiscalDocumentStatus(StrEnum):
    """Status of a fiscal document."""

    PENDING = "pending"
    EMITTED = "emitted"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    CANCELED = "canceled"
    ERROR = "error"


@dataclass(slots=True)
class FiscalDocument:
    """Fiscal document data."""

    document_type: FiscalDocumentType
    company_id: int
    series: str
    number: int
    issue_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    client_name: str = ""
    client_cnpj_cpf: str = ""
    client_address: str = ""
    items: list[dict[str, object]] = field(default_factory=list)
    total_value: Decimal = Decimal("0")
    total_taxes: Decimal = Decimal("0")
    additional_info: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.document_type, str):
            self.document_type = FiscalDocumentType(self.document_type)


@dataclass(slots=True)
class FiscalOperationResult:
    """Result of a fiscal operation."""

    success: bool
    document_id: str = ""
    protocol: str = ""
    status: FiscalDocumentStatus = FiscalDocumentStatus.PENDING
    message: str = ""
    xml_content: str = ""
    pdf_content: bytes = b""
    error_code: str = ""
    error_message: str = ""

    @classmethod
    def success_result(
        cls,
        document_id: str,
        protocol: str = "",
        xml_content: str = "",
        pdf_content: bytes = b"",
    ) -> FiscalOperationResult:
        return cls(
            success=True,
            document_id=document_id,
            protocol=protocol,
            status=FiscalDocumentStatus.AUTHORIZED,
            xml_content=xml_content,
            pdf_content=pdf_content,
        )

    @classmethod
    def error_result(
        cls,
        error_code: str,
        error_message: str,
        document_id: str = "",
    ) -> FiscalOperationResult:
        return cls(
            success=False,
            document_id=document_id,
            status=FiscalDocumentStatus.ERROR,
            error_code=error_code,
            error_message=error_message,
        )