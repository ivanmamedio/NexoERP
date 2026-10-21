"""Unit tests for the PDV presenter (no Qt) and its application queries."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from erp.modules.catalog.domain.product import Product
from erp.modules.sales.application.get_sale_state import (
    GetSaleState,
    SaleItemView,
    SaleStateOutput,
)
from erp.modules.sales.application.search_products import SearchProducts
from erp.modules.sales.presentation.pos_presenter import (
    PaymentEntry,
    PosItemRow,
    PosPresenter,
)
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound, PermissionDenied, ValidationError

# --- fakes ------------------------------------------------------------------


class FakeSaleRepository:
    def __init__(self, sale: object | None) -> None:
        self._sale = sale

    def get_by_id(self, sale_id: int, company_id: int | None = None) -> object | None:
        if company_id is not None and self._sale.company_id != company_id:
            return None
        return self._sale


class FakeItemRepository:
    def __init__(self, items: list[object]) -> None:
        self._items = items

    def list_by_sale(self, sale_id: int) -> list[object]:
        return self._items


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self._products = products

    def search(self, query: str, company_id: int | None = None, limit: int = 20) -> list[Product]:
        term = query.lower()
        return [p for p in self._products if term in p.name.lower()][:limit]


class FakeSalesServices:
    """Simula o facade de vendas mantendo um estado mínimo em memória."""

    def __init__(self) -> None:
        self.sale_id = 0
        self.items: list[dict[str, object]] = []
        self.total_cents = 0
        self.discount_cents = 0
        self.discount_calls: list[object] = []
        self.finalize_calls: list[object] = []
        self.cancel_item_calls: list[object] = []
        self.cancel_sale_calls: list[object] = []
        self.start_calls: list[object] = []
        self.search_calls: list[str] = []
        self.operator_has_discount = False
        self.supervisor_allowed = True
        self.search_results = [
            Product(id=1, sku="ARROZ-5KG", name="Arroz 5kg", price_cents=1000),
            Product(id=2, sku="ARROZ-1KG", name="Arroz 1kg", price_cents=500),
        ]

    def set_user_permissions(self, permissions: set[str]) -> None:
        self.operator_has_discount = "sale.discount" in permissions

    def start_sale(self, input_data: object) -> object:
        self.start_calls.append(input_data)
        self.sale_id += 1
        self.items = []
        self.total_cents = 0
        self.discount_cents = 0
        return SimpleNamespace(
            sale=SimpleNamespace(id=self.sale_id, company_id=getattr(input_data, "company_id", 1))
        )

    def add_item(self, input_data: object) -> object:
        query = input_data.query
        if query == "NAOEXISTE":
            raise NotFound(f"Produto '{query}' não encontrado.")
        multiplier = 1
        if "*" in query:
            prefix, rest = query.split("*", 1)
            if prefix.isdigit():
                multiplier = int(prefix)
                query = rest
        quantity = 1000 * multiplier
        line_total = 1000 * quantity // 1000
        self.items.append(
            {
                "item_id": len(self.items) + 1,
                "description": query,
                "quantity_thousandths": quantity,
                "unit": "un",
                "unit_price_cents": 1000,
                "line_total_cents": line_total,
                "cancelled": False,
            }
        )
        self._recalculate()
        return SimpleNamespace(item=SimpleNamespace(description=query))

    def apply_discount(self, input_data: object) -> object:
        self.discount_calls.append(input_data)
        if input_data.supervisor_user_id is None and not self.operator_has_discount:
            raise PermissionDenied("sem sale.discount")
        if input_data.supervisor_user_id is not None and not self.supervisor_allowed:
            raise PermissionDenied("supervisor sem permissão")
        self.discount_cents = input_data.discount_cents
        self._recalculate()
        return SimpleNamespace(sale=None, new_total_cents=self.total_cents)

    def cancel_item(self, input_data: object) -> None:
        self.cancel_item_calls.append(input_data)
        item_id = input_data.item_id
        for item in self.items:
            if item["item_id"] == item_id:
                item["cancelled"] = True
        self._recalculate()

    def cancel_sale(self, input_data: object) -> None:
        self.cancel_sale_calls.append(input_data)

    def finalize_sale(self, input_data: object) -> object:
        self.finalize_calls.append(input_data)
        paid = sum(p.amount_cents for p in input_data.payments)
        if paid < self.total_cents:
            raise ValidationError("Pagamento insuficiente.")
        change = paid - self.total_cents
        return SimpleNamespace(
            sale=SimpleNamespace(id=self.sale_id, total_cents=self.total_cents),
            change_cents=change,
        )

    def get_sale_state(self, *, sale_id: int, company_id: int | None = None) -> SaleStateOutput:
        return SaleStateOutput(
            sale_id=sale_id,
            status="draft",
            subtotal_cents=sum(
                int(i["line_total_cents"]) for i in self.items if not i["cancelled"]
            ),
            discount_cents=self.discount_cents,
            total_cents=self.total_cents,
            items=tuple(
                SaleItemView(
                    item_id=int(i["item_id"]),
                    description=str(i["description"]),
                    quantity_thousandths=int(i["quantity_thousandths"]),
                    unit=str(i["unit"]),
                    unit_price_cents=int(i["unit_price_cents"]),
                    line_total_cents=int(i["line_total_cents"]),
                    cancelled=bool(i["cancelled"]),
                )
                for i in self.items
            ),
        )

    def search_products(
        self, *, query: str, company_id: int | None = None, limit: int = 10
    ) -> list[object]:
        self.search_calls.append(query)
        term = query.lower()
        return [
            SimpleNamespace(
                product_id=p.id,
                sku=p.sku,
                name=p.name,
                price_cents=p.price_cents,
                stock_qty=p.stock_qty,
                unit=p.unit,
            )
            for p in self.search_results
            if term in p.name.lower()
        ][:limit]

    def _recalculate(self) -> None:
        subtotal = sum(int(i["line_total_cents"]) for i in self.items if not i["cancelled"])
        self.total_cents = max(0, subtotal - self.discount_cents)


class FakeSupervisorAuth:
    """Fake de SupervisorAuthPort para testes do presenter do PDV."""

    def __init__(self) -> None:
        self.supervisor_has_permission = True

    def authenticate(self, username: str, password: str):
        if username == "super" and password == "1234":
            return SimpleNamespace(user_id=2, username="super")
        return None

    def check_permission(self, *, user_id: int, permission_code: str) -> bool:
        return (
            user_id == 2 and permission_code == "sale.discount" and self.supervisor_has_permission
        )


class FakePosView:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.operators: list[str] = []
        self.item_rows: list[PosItemRow] = []
        self.totals: tuple[int, int, int] = (0, 0, 0)
        self.suggestions: list[object] = []
        self.scan_text = ""
        self.selected_item_id: int | None = None
        self.focus_calls = 0
        self.closed = False
        self.finalized: list[tuple[int, int, int]] = []
        self.payment_entries: list[PaymentEntry] | None = None
        self.discount_cents: int | None = None
        self.credentials: tuple[str, str] | None = None
        self.cancel_reason: str | None = None

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def set_operator(self, username: str) -> None:
        self.operators.append(username)

    def set_items(self, rows: list[PosItemRow]) -> None:
        self.item_rows = rows

    def set_totals(self, *, subtotal_cents: int, discount_cents: int, total_cents: int) -> None:
        self.totals = (subtotal_cents, discount_cents, total_cents)

    def set_suggestions(self, options: list[object]) -> None:
        self.suggestions = options

    def clear_scan_input(self) -> None:
        self.scan_text = ""

    def focus_scan_input(self) -> None:
        self.focus_calls += 1

    def get_scan_input(self) -> str:
        return self.scan_text

    def get_selected_item_id(self) -> int | None:
        return self.selected_item_id

    def ask_payment(self, total_cents: int) -> list[PaymentEntry] | None:
        return self.payment_entries

    def ask_discount(self, current_total_cents: int) -> int | None:
        return self.discount_cents

    def ask_supervisor_credentials(self) -> tuple[str, str] | None:
        return self.credentials

    def ask_cancel_reason(self) -> str | None:
        return self.cancel_reason

    def show_sale_finalized(self, *, sale_id: int, total_cents: int, change_cents: int) -> None:
        self.finalized.append((sale_id, total_cents, change_cents))

    def close_view(self) -> None:
        self.closed = True


def _make_presenter(
    *, session: CurrentSession | None = None, session_id: int | None = 7
) -> tuple[PosPresenter, FakePosView, FakeSalesServices, FakeSupervisorAuth]:
    view = FakePosView()
    sales = FakeSalesServices()
    supervisor_auth = FakeSupervisorAuth()
    presenter = PosPresenter(
        view=view,
        sales_services=sales,
        supervisor_auth=supervisor_auth,
        session=session or CurrentSession(user_id=1, company_id=1, username="caixa"),
        session_id=session_id,
    )
    return presenter, view, sales, supervisor_auth


# --- start ------------------------------------------------------------------


def test_start_sale_uses_open_cash_session() -> None:
    presenter, view, sales, _ = _make_presenter()

    assert presenter.start() is True

    assert len(sales.start_calls) == 1
    start_input = sales.start_calls[0]
    assert start_input.session_id == 7
    assert start_input.company_id == 1
    assert view.operators == ["caixa"]
    assert view.totals == (0, 0, 0)
    assert view.item_rows == []
    assert view.focus_calls == 1


def test_start_without_company_shows_error() -> None:
    presenter, view, sales, _ = _make_presenter(
        session=CurrentSession(user_id=1, company_id=None, username="caixa")
    )

    assert presenter.start() is False
    assert sales.start_calls == []
    assert "empresa" in view.errors[0].lower()


# --- itens ------------------------------------------------------------------


def test_add_item_refreshes_table_and_total() -> None:
    presenter, view, _, _ = _make_presenter()
    presenter.start()

    view.scan_text = "ARROZ"
    assert presenter.on_scan_entered() is True

    assert len(view.item_rows) == 1
    assert view.item_rows[0].description == "ARROZ"
    assert view.totals == (1000, 0, 1000)
    assert view.scan_text == ""
    assert view.focus_calls >= 2


def test_add_item_multiplier() -> None:
    presenter, view, _, _ = _make_presenter()
    presenter.start()

    view.scan_text = "3*ARROZ"
    assert presenter.on_scan_entered() is True

    assert view.item_rows[0].quantity_thousandths == 3000
    assert view.totals == (3000, 0, 3000)


def test_add_item_not_found_shows_error_and_keeps_sale() -> None:
    presenter, view, _, _ = _make_presenter()
    presenter.start()

    view.scan_text = "NAOEXISTE"
    assert presenter.on_scan_entered() is False

    assert view.item_rows == []
    assert "não encontrado" in view.errors[0].lower()
    assert view.scan_text == ""


def test_select_suggestion_adds_product() -> None:
    presenter, view, _, _ = _make_presenter()
    presenter.start()
    presenter.on_search_text_changed("arr")

    assert presenter.select_suggestion("ARROZ-5KG") is True
    assert view.item_rows[0].description == "ARROZ-5KG"


def test_search_suggests_after_two_characters_and_clears_short_text() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()

    presenter.on_search_text_changed("arr")
    assert sales.search_calls == ["arr"]
    assert len(view.suggestions) == 2

    presenter.on_search_text_changed("a")
    assert view.suggestions == []


def test_search_strips_multiplier_prefix() -> None:
    presenter, _, sales, _ = _make_presenter()
    presenter.start()

    presenter.on_search_text_changed("3*arr")

    assert sales.search_calls == ["arr"]


# --- pagamento --------------------------------------------------------------


def test_finalize_with_change_starts_new_sale() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.payment_entries = [PaymentEntry(method="cash", amount_cents=5000)]
    assert presenter.begin_payment() is True

    assert view.finalized == [(1, 1000, 4000)]
    assert len(sales.finalize_calls) == 1
    # Uma venda nova é aberta automaticamente após finalizar.
    assert len(sales.start_calls) == 2
    assert view.item_rows == []


def test_finalize_insufficient_payment_shows_error() -> None:
    presenter, view, _, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.payment_entries = [PaymentEntry(method="cash", amount_cents=500)]
    assert presenter.begin_payment() is False

    assert view.finalized == []
    assert "insuficiente" in view.errors[0].lower()


def test_payment_cancelled_keeps_sale_open() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.payment_entries = None
    assert presenter.begin_payment() is False
    assert sales.finalize_calls == []
    assert len(sales.start_calls) == 1


# --- desconto ---------------------------------------------------------------


def test_discount_with_operator_permission() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()
    sales.set_user_permissions({"sale.discount"})

    view.discount_cents = 100
    assert presenter.apply_discount() is True

    assert view.totals == (1000, 100, 900)
    assert view.credentials is None  # não pediu supervisor


def test_discount_without_permission_asks_supervisor_pin() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.discount_cents = 100
    view.credentials = ("super", "1234")
    assert presenter.apply_discount() is True

    assert len(sales.discount_calls) == 2
    retry = sales.discount_calls[1]
    assert retry.supervisor_user_id == 2
    assert retry.supervisor_username == "super"
    assert view.totals == (1000, 100, 900)


def test_discount_with_invalid_supervisor_shows_error() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.discount_cents = 100
    view.credentials = ("super", "errada")
    assert presenter.apply_discount() is False

    assert len(sales.discount_calls) == 1
    assert "inválidos" in view.errors[0].lower()


def test_discount_supervisor_without_permission_shows_error() -> None:
    presenter, view, sales, supervisor_auth = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()
    supervisor_auth.supervisor_has_permission = False

    view.discount_cents = 100
    view.credentials = ("super", "1234")
    assert presenter.apply_discount() is False

    assert len(sales.discount_calls) == 1
    assert "sale.discount" in view.errors[0]


# --- cancelamento -----------------------------------------------------------


def test_cancel_item_requires_selection() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()

    assert presenter.cancel_selected_item() is False
    assert sales.cancel_item_calls == []
    assert "selecione" in view.errors[0].lower()


def test_cancel_selected_item_updates_total() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.selected_item_id = 1
    view.cancel_reason = "erro"
    assert presenter.cancel_selected_item() is True

    assert len(sales.cancel_item_calls) == 1
    assert view.item_rows == []
    assert view.totals == (0, 0, 0)


def test_cancel_sale_starts_a_new_sale() -> None:
    presenter, view, sales, _ = _make_presenter()
    presenter.start()
    view.scan_text = "ARROZ"
    presenter.on_scan_entered()

    view.cancel_reason = "cliente desistiu"
    assert presenter.cancel_sale() is True

    assert len(sales.cancel_sale_calls) == 1
    assert len(sales.start_calls) == 2


def test_escape_closes_view() -> None:
    presenter, view, _, _ = _make_presenter()

    presenter.on_escape()

    assert view.closed is True


# --- application queries ----------------------------------------------------


def test_get_sale_state_maps_items() -> None:
    sale = SimpleNamespace(
        id=10,
        status="draft",
        subtotal_cents=5000,
        discount_cents=500,
        total_cents=4500,
    )
    item = SimpleNamespace(
        id=3,
        description="Arroz 5kg",
        quantity_thousandths=2000,
        unit="un",
        unit_price_cents=2500,
        line_total_cents=5000,
        cancelled=False,
    )
    output = GetSaleState(
        FakeSaleRepository(sale),
        FakeItemRepository([item]),  # type: ignore[arg-type]
    ).execute(10)

    assert output.sale_id == 10
    assert output.total_cents == 4500
    assert output.items == (
        SaleItemView(
            item_id=3,
            description="Arroz 5kg",
            quantity_thousandths=2000,
            unit="un",
            unit_price_cents=2500,
            line_total_cents=5000,
            cancelled=False,
        ),
    )


def test_get_sale_state_not_found() -> None:
    with pytest.raises(NotFound):
        GetSaleState(
            FakeSaleRepository(None),
            FakeItemRepository([]),  # type: ignore[arg-type]
        ).execute(99)


def test_search_products_maps_results() -> None:
    repo = FakeProductRepository(
        [Product(id=1, sku="ARROZ-5KG", name="Arroz 5kg", price_cents=2500)]
    )

    results = SearchProducts(repo).execute(query="arr", company_id=1)  # type: ignore[arg-type]

    assert len(results) == 1
    assert results[0].sku == "ARROZ-5KG"
    assert results[0].price_cents == 2500
