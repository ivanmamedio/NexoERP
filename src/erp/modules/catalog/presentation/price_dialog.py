"""Price table dialog for product pricing management."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from erp.modules.catalog.application.services import CatalogServices
from erp.modules.catalog.domain.product import Product
from erp.shared.application.session import CurrentSession

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class PriceTableModel(QAbstractTableModel):
    """Modelo para a tabela de preços com suporte a ordenação."""

    def __init__(self, products: list[Product]) -> None:
        super().__init__()
        self._products = products

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        _ = parent
        return len(self._products)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        _ = parent
        return 7

    def data(self, index: QModelIndex, role: int) -> object:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        product = self._products[index.row()]
        column = index.column()
        if column == 0:
            return product.sku
        if column == 1:
            return product.name
        if column == 2:
            return f"R$ {product.cost_cents / 100:.2f}"
        if column == 3:
            return f"R$ {product.price_cents / 100:.2f}"
        if column == 4:
            # Margem sobre preço de venda: ((venda - custo) / venda) * 100
            if product.price_cents > 0:
                margin = ((product.price_cents - product.cost_cents) * 100.0 / product.price_cents)
                return f"{margin:.2f}%"
            return "0.00%"
        if column == 5:
            return product.unit
        if column == 6:
            return "Sim" if product.active else "Não"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> object | None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (
                "Código (SKU)",
                "Descrição",
                "Preço de Custo",
                "Preço de Venda",
                "Margem %",
                "Unidade",
                "Status",
            )[section]
        return None

    def get_product_at(self, row: int) -> Product | None:
        if 0 <= row < len(self._products):
            return self._products[row]
        return None


class PriceEditDialog(QDialog):
    """Diálogo para editar preço e margem do produto."""

    def __init__(
        self,
        product: Product,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._product = product

        self.setWindowTitle(f"Editar Preço: {product.name}")
        self.setModal(True)
        self.resize(450, 350)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Info do produto (readonly)
        self._sku_label = QLabel(self._product.sku)
        form.addRow("SKU:", self._sku_label)

        self._name_label = QLabel(self._product.name)
        form.addRow("Produto:", self._name_label)

        self._unit_label = QLabel(self._product.unit)
        form.addRow("Unidade:", self._unit_label)

        # Custo
        self._cost_spin = QDoubleSpinBox()
        self._cost_spin.setRange(0.0, 999999.99)
        self._cost_spin.setDecimals(2)
        self._cost_spin.setSuffix(" R$")
        self._cost_spin.setGroupSeparatorShown(True)
        self._cost_spin.setSingleStep(0.01)
        self._cost_spin.setValue(self._product.cost_cents / 100)
        form.addRow("Preço de Custo (R$):", self._cost_spin)

        # Margem
        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0.0, 10000.0)
        self._margin_spin.setDecimals(2)
        self._margin_spin.setSuffix(" %")
        self._margin_spin.setGroupSeparatorShown(True)
        self._margin_spin.setSingleStep(0.1)
        # Carregar margem atual
        current_margin = self._product.margin_pct / 100  # stored as basis points
        self._margin_spin.setValue(current_margin)
        form.addRow("Margem (%):", self._margin_spin)

        # Preço de venda
        self._price_spin = QDoubleSpinBox()
        self._price_spin.setRange(0.0, 999999.99)
        self._price_spin.setDecimals(2)
        self._price_spin.setSuffix(" R$")
        self._price_spin.setGroupSeparatorShown(True)
        self._price_spin.setSingleStep(0.01)
        self._price_spin.setValue(self._product.price_cents / 100)
        form.addRow("Preço de Venda (R$):", self._price_spin)

        # Auto-calculate price from cost + margin
        self._cost_spin.valueChanged.connect(self._on_cost_or_margin_changed)
        self._margin_spin.valueChanged.connect(self._on_cost_or_margin_changed)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("Salvar")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _on_cost_or_margin_changed(self) -> None:
        cost = self._cost_spin.value()
        margin_pct = self._margin_spin.value()
        if cost > 0 and margin_pct >= 0:
            # Preço = Custo / (1 - margem/100) quando margem é sobre preço de venda
            # Ou Preço = Custo * (1 + margem/100) quando margem é sobre custo
            # O sistema usa margem sobre preço de venda: margem = (preco - custo) / preco
            # Logo: preco = custo / (1 - margem/100)
            if margin_pct < 100:
                price = cost / (1 - margin_pct / 100)
                self._price_spin.setValue(round(price, 2))

    def _on_save_clicked(self) -> None:
        self.accept()

    def get_values(self) -> tuple[int, int, int]:
        """Retorna (cost_cents, margin_pct_basis_points, price_cents)."""
        cost_cents = int(round(self._cost_spin.value() * 100))
        margin_pct = int(round(self._margin_spin.value() * 100))  # basis points
        price_cents = int(round(self._price_spin.value() * 100))
        return cost_cents, margin_pct, price_cents


class PriceTableWidget(QWidget):
    """Widget principal da tabela de preços."""

    def __init__(
        self,
        services: CatalogServices,
        session: CurrentSession,
        engine: Engine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._session = session
        self._engine = engine

        self._setup_ui()
        self._load_products()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Buscar por SKU, nome...")
        self._search_edit.setMinimumWidth(200)
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_edit)

        toolbar.addStretch()

        self._btn_refresh = QPushButton("Atualizar")
        self._btn_refresh.clicked.connect(self._load_products)
        toolbar.addWidget(self._btn_refresh)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.doubleClicked.connect(self._on_edit_price)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # Proxy model for filtering
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(-1)
        self._table.setModel(self._proxy_model)

        layout.setContentsMargins(8, 8, 8, 8)

    def _load_products(self) -> None:
        try:
            output = self._services.list_low_stock(company_id=self._session.company_id)
            self._source_model = PriceTableModel(output.products)
            self._proxy_model.setSourceModel(self._source_model)
            self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self._table.horizontalHeader().setStretchLastSection(True)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos: {exc}")

    def _on_search_changed(self, text: str) -> None:
        self._proxy_model.setFilterFixedString(text)

    def _on_selection_changed(self) -> None:
        has_selection = self._table.selectionModel().hasSelection()
        # Could enable actions here

    def _on_edit_price(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        product = self._source_model.get_product_at(source_index.row())
        if product is None:
            return

        dialog = PriceEditDialog(product, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cost_cents, margin_pct, price_cents = dialog.get_values()
            try:
                from erp.modules.catalog.application.update_product import UpdateProductInput
                self._services.update_product(
                    UpdateProductInput(
                        product_id=product.id,
                        cost_cents=cost_cents,
                        margin_pct=margin_pct,
                        price_cents=price_cents,
                        company_id=self._session.company_id,
                    )
                )
                self._load_products()
                QMessageBox.information(self, "Sucesso", "Preço atualizado com sucesso!")
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar preço: {exc}")

    def set_products(self, products: list[Product]) -> None:
        self._source_model = PriceTableModel(products)
        self._proxy_model.setSourceModel(self._source_model)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)


def create_price_dialog(
    services: CatalogServices,
    session: CurrentSession,
    engine: Engine,
    parent: QWidget | None = None,
) -> QDialog:
    """Factory para criar o diálogo de tabela de preços."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Tabela de Formação de Preço")
    dialog.resize(1000, 600)

    layout = QVBoxLayout(dialog)

    widget = PriceTableWidget(services, session, engine, dialog)
    layout.addWidget(widget)

    btn_close = QPushButton("Fechar")
    btn_close.clicked.connect(dialog.accept)
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(btn_close)
    layout.addLayout(btn_layout)

    return dialog