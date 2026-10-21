"""Apply discount use case — sale.discount permission OR supervisor PIN."""

from __future__ import annotations

from erp.modules.sales.application.ports import SaleRepository
from erp.modules.sales.domain.sale import Sale
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError


class ApplyDiscountInput:
    def __init__(
        self,
        *,
        sale_id: int,
        discount_cents: int,
        user_id: int | None,
        username: str,
        supervisor_user_id: int | None = None,
        supervisor_username: str = "",
        company_id: int | None = None,
    ) -> None:
        self.sale_id = sale_id
        self.discount_cents = discount_cents
        self.user_id = user_id
        self.username = username
        self.supervisor_user_id = supervisor_user_id
        self.supervisor_username = supervisor_username
        self.company_id = company_id


class ApplyDiscountOutput:
    def __init__(self, sale: Sale, new_total_cents: int) -> None:
        self.sale = sale
        self.new_total_cents = new_total_cents


class ApplyDiscount:
    """Aplica desconto. Exige sale.discount OU autorização de supervisor via PIN."""

    def __init__(
        self,
        repository: SaleRepository,
        user_permissions: set[str],
    ) -> None:
        self._repository = repository
        self._user_permissions = user_permissions

    def execute(self, input: ApplyDiscountInput) -> ApplyDiscountOutput:
        sale = self._repository.get_by_id(input.sale_id, company_id=input.company_id)
        if sale is None:
            raise NotFound(f"Venda {input.sale_id} não encontrada.")
        if not sale.is_draft():
            raise ValidationError("Venda não está mais aberta.")

        has_permission = "sale.discount" in self._user_permissions
        has_supervisor = input.supervisor_user_id is not None and input.supervisor_username != ""

        if not has_permission and not has_supervisor:
            raise PermissionDenied(
                "Desconto exige permissão sale.discount ou autorização de supervisor."
            )

        if has_supervisor:
            sale.authorized_by_user_id = input.supervisor_user_id
            sale.authorized_by_username = input.supervisor_username

        sale.apply_discount(input.discount_cents)
        self._repository.save(sale)

        return ApplyDiscountOutput(sale=sale, new_total_cents=sale.total_cents)
