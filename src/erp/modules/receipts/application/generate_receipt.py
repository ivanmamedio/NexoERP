"""Receipt generator use case — builds a non-fiscal receipt from sale data."""

from __future__ import annotations

from dataclasses import dataclass

from erp.modules.receipts.application.ports import CompanySettingsPort, ReceiptRepositoryPort
from erp.modules.receipts.domain import Receipt, ReceiptLine


@dataclass(slots=True, frozen=True)
class GenerateReceiptInput:
    """Dados de entrada para gerar o cupom."""

    sale_id: int
    company_id: int
    terminal_code: str
    operator_name: str
    operator_id: int


@dataclass(slots=True, frozen=True)
class GenerateReceiptOutput:
    """Resultado da geração do cupom."""

    receipt: Receipt


class ReceiptGenerator:
    """Gera o cupom não fiscal a partir dos dados da venda."""

    def __init__(
        self,
        receipt_repo: ReceiptRepositoryPort,
        company_settings: CompanySettingsPort,
    ) -> None:
        self._receipt_repo = receipt_repo
        self._company_settings = company_settings

    def execute(self, input_data: GenerateReceiptInput) -> GenerateReceiptOutput:
        company_name, tax_id, address, phone, header_lines, footer_lines = (
            self._company_settings.get_company_header(input_data.company_id)
        )

        receipt = Receipt(
            company_name=company_name,
            company_tax_id=tax_id,
            company_address=address,
            company_phone=phone,
            header_lines=header_lines,
            footer_lines=footer_lines,
            terminal_code=input_data.terminal_code,
            operator_name=input_data.operator_name,
        )

        self._receipt_repo.save(receipt)
        return GenerateReceiptOutput(receipt=receipt)


class ReceiptFormatter:
    """Formata o cupom para impressão (largura fixa 32 ou 48 colunas)."""

    WIDTH_58MM = 32  # caracteres por linha para 58mm
    WIDTH_80MM = 48  # caracteres por linha para 80mm

    def __init__(self, width: int = WIDTH_80MM) -> None:
        self.width = width
        self._item_w = max(1, width - 30)
        self._qtd_w = 6
        self._un_w = 4
        self._price_w = 10
        self._total_w = 10

    def format_receipt(self, receipt: Receipt) -> str:
        """Formata o cupom completo como texto."""
        lines = []

        # Cabeçalho
        lines.append(self._center(receipt.company_name))
        if receipt.company_tax_id:
            lines.append(self._center(f"CNPJ: {receipt.company_tax_id}"))
        if receipt.company_address:
            lines.append(self._center(receipt.company_address))
        if receipt.company_phone:
            lines.append(self._center(f"Tel: {receipt.company_phone}"))

        lines.append(self._hr())

        # Info da venda
        lines.append(f"Venda: {receipt.sale_id or '-'}")
        lines.append(f"Terminal: {receipt.terminal_code or '-'}")
        lines.append(f"Operador: {receipt.operator_name or '-'}")
        opened_at_str = receipt.opened_at.strftime("%d/%m/%Y %H:%M") if receipt.opened_at else "-"
        lines.append(f"Abertura: {opened_at_str}")
        if receipt.closed_at:
            closed_at_str = receipt.closed_at.strftime("%d/%m/%Y %H:%M")
            lines.append(f"Fechamento: {closed_at_str}")

        lines.append(self._hr())

        # Linha "NÃO É DOCUMENTO FISCAL" em destaque
        lines.append(self._center(receipt.non_fiscal_line))
        lines.append(self._hr())

        # Cabeçalho da tabela de itens
        lines.append(self._format_line("Item", "Qtd", "Un", "Preço", "Total"))
        lines.append(self._hr())

        # Itens
        for line in receipt.lines:
            lines.append(self._format_item_line(line))

        lines.append(self._hr())

        # Totais
        lines.append(self._format_line("", "", "", "TOTAL:", receipt.total.format_brl()))
        lines.append(self._hr())

        # Formas de pagamento
        for method, amount in receipt.payment_methods:
            lines.append(self._format_line(method.upper(), "", "", "", amount.format_brl()))

        if receipt.change.cents > 0:
            lines.append(self._hr())
            lines.append(self._format_line("TROCO:", "", "", "", receipt.change.format_brl()))

        lines.append(self._hr())

        # Rodapé
        for footer in receipt.footer_lines:
            lines.append(self._center(footer))

        lines.append(self._center("Obrigado pela preferência!"))
        lines.append(self._center("Volte sempre!"))

        return "\n".join(lines)

    def _center(self, text: str) -> str:
        return text.center(self.width)

    def _hr(self) -> str:
        return "-" * self.width

    def _format_line(self, *parts: str) -> str:
        """Formata uma linha com larguras fixas."""
        item_w = max(1, self.width - 30)
        qtd_w = 6
        un_w = 4
        price_w = 10
        total_w = 10

        return (
            parts[0][:item_w].ljust(item_w)
            + parts[1].rjust(qtd_w)
            + parts[2].center(un_w)
            + parts[3].rjust(price_w)
            + parts[4].rjust(total_w)
        )

    def _format_item_line(self, line: ReceiptLine) -> str:
        """Formata uma linha de item."""
        qty_str = f"{line.quantity:.3f}".rstrip("0").rstrip(".")
        if qty_str.endswith("."):
            qty_str = qty_str[:-1]

        return self._format_line(
            line.description[: self._item_w],
            qty_str.rjust(self._qtd_w),
            line.unit.center(self._un_w),
            line.unit_price.format_brl().rjust(self._price_w),
            line.total.format_brl().rjust(self._total_w),
        )
