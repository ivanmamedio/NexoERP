"""Ports (interfaces) for the receipts module."""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from erp.modules.receipts.domain import Receipt


@runtime_checkable
class ReceiptPrinterPort(Protocol):
    """Porta para impressão de cupons (implementada por adapters
    ESC/POS, Windows, CUPS, Preview)."""

    @abstractmethod
    def print_receipt(self, receipt: Receipt) -> None:
        """Imprime o cupom na impressora configurada."""
        ...

    @abstractmethod
    def open_cash_drawer(self) -> None:
        """Envia comando de abertura de gaveta."""
        ...


@runtime_checkable
class ReceiptRepositoryPort(Protocol):
    """Porta para persistência de cupons (opcional, para auditoria)."""

    @abstractmethod
    def save(self, receipt: Receipt) -> None:
        """Salva o cupom para auditoria."""
        ...

    @abstractmethod
    def get_by_id(self, receipt_id: int) -> Receipt | None:
        """Recupera um cupom pelo ID."""
        ...

    @abstractmethod
    def list_by_sale(self, sale_id: int) -> list[Receipt]:
        """Lista cupons de uma venda."""
        ...


@runtime_checkable
class CompanySettingsPort(Protocol):
    """Porta para obter configurações da empresa (cabeçalho/rodapé do cupom)."""

    @abstractmethod
    def get_company_header(
        self, company_id: int
    ) -> tuple[str, str, str, str, list[str], list[str]]:
        """Retorna (nome, cnpj, endereço, telefone, header_lines, footer_lines)."""
        ...