"""Receipt formatter — formats receipt for printing (fixed width 32 or 48 columns)."""

from __future__ import annotations

from erp.modules.receipts.domain import Receipt, ReceiptLine


class ReceiptFormatter:
    """Formats receipt for printing (fixed width 32 or 48 columns)."""

    WIDTH_58MM = 32
    WIDTH_80MM = 48

    def __init__(self, width: int = WIDTH_80MM) -> None:
        self.width = width
        self._item_w = max(1, width - 30)
        self._qtd_w = 6
        self._un_w = 4
        self._price_w = 10
        self._total_w = 10

    def format_receipt(self, receipt: Receipt) -> str:
        """Formats the complete receipt as text."""
        lines = []

        # Header
        lines.append(self._center(receipt.company_name))
        if receipt.company_tax_id:
            lines.append(self._center(f"CNPJ: {receipt.company_tax_id}"))
        if receipt.company_address:
            lines.append(self._center(receipt.company_address))
        if receipt.company_phone:
            lines.append(self._center(f"Tel: {receipt.company_phone}"))

        lines.append(self._hr())

        # Sale info
        lines.append(f"Venda: {receipt.sale_id or '-'}")
        lines.append(f"Terminal: {receipt.terminal_code or '-'}")
        lines.append(f"Operador: {receipt.operator_name or '-'}")
        if receipt.opened_at:
            lines.append(f"Abertura: {receipt.opened_at.strftime('%d/%m/%Y %H:%M')}")
        if receipt.closed_at:
            lines.append(f"Fechamento: {receipt.closed_at.strftime('%d/%m/%Y %H:%M')}")

        lines.append(self._hr())

        # "NÃO É DOCUMENTO FISCAL" in highlight
        lines.append(self._center(receipt.non_fiscal_line))
        lines.append(self._hr())

        # Items header
        lines.append(self._format_line("Item", "Qtd", "Un", "Preço", "Total"))
        lines.append(self._hr())

        # Items
        for line in receipt.lines:
            lines.append(self._format_item_line(line))

        lines.append(self._hr())

        # Totals
        lines.append(self._format_line("", "", "", "TOTAL:", receipt.total.format_brl()))
        lines.append(self._hr())

        # Payment methods
        for method, amount in receipt.payment_methods:
            lines.append(self._format_line(method.upper(), "", "", "", amount.format_brl()))

        if receipt.change.cents > 0:
            lines.append(self._hr())
            lines.append(self._format_line("TROCO:", "", "", "", receipt.change.format_brl()))

        lines.append(self._hr())

        # Footer
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
        """Formats a line with fixed widths."""
        return (
            parts[0][: self._item_w].ljust(self._item_w)
            + parts[1].rjust(self._qtd_w)
            + parts[2].center(self._un_w)
            + parts[3].rjust(self._price_w)
            + parts[4].rjust(self._total_w)
        )

    def _format_item_line(self, line: ReceiptLine) -> str:
        """Formats a single item line."""
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
