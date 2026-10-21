"""PDV presenter — orquestra a venda sem depender de Qt.

A view implementa este contrato (inclusive abrindo os diálogos de pagamento,
desconto e credenciais do supervisor) e o presenter concentra as regras de
fluxo. Nenhuma regra de negócio mora nos widgets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from erp.modules.sales.application.add_item import AddItemInput
from erp.modules.sales.application.apply_discount import ApplyDiscountInput
from erp.modules.sales.application.cancel_sale import (
    CancelItemInput,
    CancelSaleInput,
)
from erp.modules.sales.application.finalize_sale import (
    FinalizePaymentInput,
    FinalizeSaleInput,
)
from erp.modules.sales.application.get_sale_state import SaleStateOutput
from erp.modules.sales.application.ports import SupervisorAuthPort
from erp.modules.sales.application.services import SalesServices
from erp.modules.sales.application.start_sale import StartSaleInput
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import DomainError, PermissionDenied

#: Código de permissão que autoriza desconto sem supervisor.
_DISCOUNT_PERMISSION = "sale.discount"


@dataclass(slots=True, frozen=True)
class PosItemRow:
    """Linha da tabela de itens do PDV."""

    item_id: int
    description: str
    quantity_thousandths: int
    unit: str
    unit_price_cents: int
    line_total_cents: int


@dataclass(slots=True, frozen=True)
class ProductOption:
    """Sugestão de produto exibida durante a digitação do nome."""

    product_id: int
    sku: str
    name: str
    price_cents: int
    stock_qty: int
    unit: str


@dataclass(slots=True, frozen=True)
class PaymentEntry:
    """Pagamento informado na view (será convertido em FinalizePaymentInput)."""

    method: str
    amount_cents: int


@runtime_checkable
class PosView(Protocol):
    """Contrato da tela do PDV."""

    def show_error(self, message: str) -> None: ...
    def set_operator(self, username: str) -> None: ...
    def set_items(self, rows: list[PosItemRow]) -> None: ...
    def set_totals(self, *, subtotal_cents: int, discount_cents: int, total_cents: int) -> None: ...
    def set_suggestions(self, options: list[ProductOption]) -> None: ...
    def clear_scan_input(self) -> None: ...
    def focus_scan_input(self) -> None: ...
    def get_scan_input(self) -> str: ...
    def get_selected_item_id(self) -> int | None: ...
    def ask_payment(self, total_cents: int) -> list[PaymentEntry] | None: ...
    def ask_discount(self, current_total_cents: int) -> int | None: ...
    def ask_supervisor_credentials(self) -> tuple[str, str] | None: ...
    def ask_cancel_reason(self) -> str | None: ...
    def show_sale_finalized(self, *, sale_id: int, total_cents: int, change_cents: int) -> None: ...
    def close_view(self) -> None: ...


class PosPresenter:
    """Fluxo completo do PDV: venda, itens, desconto, cancelamento e pagamento."""

    def __init__(
        self,
        *,
        view: PosView,
        sales_services: SalesServices,
        supervisor_auth: SupervisorAuthPort,
        session: CurrentSession,
        session_id: int | None = None,
    ) -> None:
        self._view = view
        self._sales_services = sales_services
        self._supervisor_auth = supervisor_auth
        self._session = session
        self._session_id = session_id
        self._sale_id: int | None = None
        self._suggestions: list[ProductOption] = []

    # --- ciclo de vida ------------------------------------------------------

    def start(self) -> bool:
        """Inicia uma nova venda para o operador logado."""
        if self._session.user_id is None:
            self._view.show_error("Sessão não autenticada.")
            return False
        if self._session.company_id is None:
            self._view.show_error("Nenhuma empresa ativa na sessão.")
            return False

        try:
            output = self._sales_services.start_sale(
                StartSaleInput(
                    user_id=self._session.user_id,
                    username=self._session.username or "",
                    session_id=self._session_id,
                    company_id=self._session.company_id,
                )
            )
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro ao iniciar venda: {exc}")
            return False

        self._sale_id = output.sale.id
        self._view.set_operator(self._session.username or "")
        self._refresh()
        self._view.focus_scan_input()
        return True

    def on_escape(self) -> None:
        """Esc: volta (fecha) a tela do PDV."""
        self._view.close_view()

    # --- itens --------------------------------------------------------------

    def on_scan_entered(self) -> bool:
        """Enter no campo de leitura: adiciona por código/SKU/nome ou '3*código'."""
        self._view.set_suggestions([])
        self._suggestions = []
        sale_id = self._sale_id
        if sale_id is None:
            self._view.show_error("Nenhuma venda aberta.")
            return False

        query = self._view.get_scan_input().strip()
        if not query:
            self._view.focus_scan_input()
            return False

        try:
            self._sales_services.add_item(
                AddItemInput(
                    sale_id=sale_id,
                    query=query,
                    company_id=self._session.company_id,
                )
            )
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.clear_scan_input()
            self._view.focus_scan_input()
            return False
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro inesperado: {exc}")
            self._view.clear_scan_input()
            self._view.focus_scan_input()
            return False

        self._view.clear_scan_input()
        self._refresh()
        self._view.focus_scan_input()
        return True

    def on_search_text_changed(self, text: str) -> None:
        """Chamado pela view após o debounce: sugere produtos pelo nome."""
        query = text.strip()
        # Ignora o prefixo do multiplicador ("3*arr" -> "arr").
        if "*" in query:
            prefix, rest = query.split("*", 1)
            if prefix.strip().isdigit():
                query = rest.strip()

        if len(query) < 2:
            self._suggestions = []
            self._view.set_suggestions([])
            return

        try:
            found = self._sales_services.search_products(
                query=query,
                company_id=self._session.company_id,
                limit=10,
            )
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro na busca: {exc}")
            return

        self._suggestions = [
            ProductOption(
                product_id=item.product_id,
                sku=item.sku,
                name=item.name,
                price_cents=item.price_cents,
                stock_qty=item.stock_qty,
                unit=item.unit,
            )
            for item in found
        ]
        self._view.set_suggestions(self._suggestions)

    def select_suggestion(self, sku: str) -> bool:
        """Adiciona o produto escolhido na lista de sugestões (pelo SKU)."""
        if not any(option.sku == sku for option in self._suggestions):
            self._view.show_error("Sugestão de produto inválida.")
            return False
        self._view.clear_scan_input()
        self._view.set_suggestions([])
        self._suggestions = []
        return self._add_by_sku(sku)

    def _add_by_sku(self, sku: str) -> bool:
        sale_id = self._sale_id
        if sale_id is None:
            self._view.show_error("Nenhuma venda aberta.")
            return False
        try:
            self._sales_services.add_item(
                AddItemInput(
                    sale_id=sale_id,
                    query=sku,
                    company_id=self._session.company_id,
                )
            )
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.focus_scan_input()
            return False
        self._refresh()
        self._view.focus_scan_input()
        return True

    # --- desconto -----------------------------------------------------------

    def apply_discount(self) -> bool:
        """F4: aplica desconto; se negado, pede autorização do supervisor."""
        state = self._current_state()
        if state is None:
            return False

        discount_cents = self._view.ask_discount(state.total_cents)
        if discount_cents is None:
            self._view.focus_scan_input()
            return False
        if discount_cents < 0:
            self._view.show_error("Desconto não pode ser negativo.")
            self._view.focus_scan_input()
            return False

        sale_id = self._sale_id
        assert sale_id is not None  # garantido por _current_state
        base_input = ApplyDiscountInput(
            sale_id=sale_id,
            discount_cents=discount_cents,
            user_id=self._session.user_id,
            username=self._session.username or "",
            company_id=self._session.company_id,
        )

        try:
            self._sales_services.apply_discount(base_input)
        except PermissionDenied:
            supervisor = self._authorize_supervisor()
            if supervisor is None:
                self._view.focus_scan_input()
                return False
            supervisor_id, supervisor_name = supervisor
            try:
                self._sales_services.apply_discount(
                    ApplyDiscountInput(
                        sale_id=sale_id,
                        discount_cents=discount_cents,
                        user_id=self._session.user_id,
                        username=self._session.username or "",
                        supervisor_user_id=supervisor_id,
                        supervisor_username=supervisor_name,
                        company_id=self._session.company_id,
                    )
                )
            except DomainError as exc:
                self._view.show_error(str(exc))
                self._view.focus_scan_input()
                return False
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.focus_scan_input()
            return False

        self._refresh()
        self._view.focus_scan_input()
        return True

    def _authorize_supervisor(self) -> tuple[int, str] | None:
        """Valida credenciais e a permissão sale.discount do supervisor."""
        credentials = self._view.ask_supervisor_credentials()
        if credentials is None:
            return None
        username, password = credentials
        try:
            auth = self._supervisor_auth.authenticate(username, password)
        except Exception:
            self._view.show_error("Supervisor ou senha inválidos.")
            return None
        if auth is None:
            self._view.show_error("Supervisor ou senha inválidos.")
            return None
        if not self._supervisor_auth.check_permission(
            user_id=auth.user_id, permission_code=_DISCOUNT_PERMISSION
        ):
            self._view.show_error("Supervisor não possui permissão de desconto (sale.discount).")
            return None
        return auth.user_id, auth.username

    # --- cancelamento -------------------------------------------------------

    def cancel_selected_item(self) -> bool:
        """F6: cancela o item selecionado (exige sale.cancel no caso de uso)."""
        sale_id = self._sale_id
        if sale_id is None:
            self._view.show_error("Nenhuma venda aberta.")
            return False
        item_id = self._view.get_selected_item_id()
        if item_id is None:
            self._view.show_error("Selecione um item para cancelar.")
            self._view.focus_scan_input()
            return False
        reason = self._view.ask_cancel_reason()
        if reason is None:
            self._view.focus_scan_input()
            return False

        try:
            self._sales_services.cancel_item(
                CancelItemInput(
                    item_id=item_id,
                    reason=reason,
                    user_id=self._session.user_id,
                    username=self._session.username or "",
                )
            )
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.focus_scan_input()
            return False

        self._refresh()
        self._view.focus_scan_input()
        return True

    def cancel_sale(self) -> bool:
        """F8: cancela a venda inteira (exige sale.cancel no caso de uso)."""
        sale_id = self._sale_id
        if sale_id is None:
            self._view.show_error("Nenhuma venda aberta.")
            return False
        reason = self._view.ask_cancel_reason()
        if reason is None:
            self._view.focus_scan_input()
            return False

        try:
            self._sales_services.cancel_sale(
                CancelSaleInput(
                    sale_id=sale_id,
                    reason=reason,
                    user_id=self._session.user_id,
                    username=self._session.username or "",
                    company_id=self._session.company_id,
                )
            )
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.focus_scan_input()
            return False

        return self.start()

    # --- pagamento ----------------------------------------------------------

    def begin_payment(self) -> bool:
        """F2: abre o pagamento misto e finaliza a venda."""
        state = self._current_state()
        if state is None:
            return False
        sale_id = self._sale_id
        assert sale_id is not None
        if not [item for item in state.items if not item.cancelled]:
            self._view.show_error("Venda sem itens.")
            self._view.focus_scan_input()
            return False

        entries = self._view.ask_payment(state.total_cents)
        if entries is None:
            self._view.focus_scan_input()
            return False

        payments = [
            FinalizePaymentInput(method=entry.method, amount_cents=entry.amount_cents)
            for entry in entries
            if entry.amount_cents > 0
        ]
        try:
            output = self._sales_services.finalize_sale(
                FinalizeSaleInput(
                    sale_id=sale_id,
                    payments=payments,
                    user_id=self._session.user_id,
                    username=self._session.username or "",
                    session_id=self._session_id,
                    company_id=self._session.company_id,
                )
            )
        except DomainError as exc:
            self._view.show_error(str(exc))
            self._view.focus_scan_input()
            return False
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro inesperado: {exc}")
            self._view.focus_scan_input()
            return False

        self._view.show_sale_finalized(
            sale_id=output.sale.id or 0,
            total_cents=output.sale.total_cents,
            change_cents=output.change_cents,
        )
        self._sale_id = None
        return self.start()

    # --- helpers ------------------------------------------------------------

    def _current_state(self) -> SaleStateOutput | None:
        sale_id = self._sale_id
        if sale_id is None:
            self._view.show_error("Nenhuma venda aberta.")
            return None
        try:
            return self._sales_services.get_sale_state(sale_id=sale_id)
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro ao carregar venda: {exc}")
            return None

    def _refresh(self) -> None:
        if self._sale_id is None:
            return
        try:
            state = self._sales_services.get_sale_state(sale_id=self._sale_id)
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro ao carregar venda: {exc}")
            return
        self._view.set_totals(
            subtotal_cents=state.subtotal_cents,
            discount_cents=state.discount_cents,
            total_cents=state.total_cents,
        )
        self._view.set_items(
            [
                PosItemRow(
                    item_id=item.item_id,
                    description=item.description,
                    quantity_thousandths=item.quantity_thousandths,
                    unit=item.unit,
                    unit_price_cents=item.unit_price_cents,
                    line_total_cents=item.line_total_cents,
                )
                for item in state.items
                if not item.cancelled
            ]
        )
