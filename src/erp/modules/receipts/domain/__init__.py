"""Receipt domain entity and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from erp.shared.domain.entities import Entity
from erp.shared.domain.value_objects import Money


@dataclass(slots=True)
class ReceiptLine:
    """Uma linha do cupom (descrição, quantidade, preço unitário, total)."""

    description: str
    quantity: float
    unit: str
    unit_price: Money
    total: Money

    def __post_init__(self) -> None:
        if isinstance(self.unit_price, int):
            self.unit_price = Money(self.unit_price)
        if isinstance(self.total, int):
            self.total = Money(self.total)


@dataclass(slots=True)
class Receipt(Entity):
    """Cupom não fiscal com cabeçalho, itens, rodapé e linha 'NÃO É DOCUMENTO FISCAL'."""

    company_name: str = ""
    company_tax_id: str = ""
    company_address: str = ""
    company_phone: str = ""
    header_lines: list[str] = field(default_factory=list)
    footer_lines: list[str] = field(default_factory=list)
    lines: list[ReceiptLine] = field(default_factory=list)
    sale_id: int | None = None
    operator_name: str = ""
    terminal_code: str = ""
    opened_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None
    payment_methods: list[tuple[str, Money]] = field(default_factory=list)
    total: Money = field(default_factory=lambda: Money(0))
    change: Money = field(default_factory=lambda: Money(0))
    non_fiscal_line: str = "NÃO É DOCUMENTO FISCAL"

    def add_line(self, description: str, quantity: float, unit: str, unit_price: Money) -> None:
        """Adiciona uma linha ao cupom."""
        total = Money(int(unit_price.cents * quantity))
        self.lines.append(
            ReceiptLine(
                description=description,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                total=total,
            )
        )
        self.total = Money(self.total.cents + total.cents)

    def add_payment(self, method: str, amount: Money) -> None:
        """Registra uma forma de pagamento."""
        self.payment_methods.append((method, amount))

    def set_change(self, change: Money) -> None:
        """Define o troco."""
        self.change = change

    def close(self) -> None:
        """Fecha o cupom registrando o horário de fechamento."""
        self.closed_at = datetime.now(UTC)

    @property
    def is_closed(self) -> bool:
        return self.closed_at is not None