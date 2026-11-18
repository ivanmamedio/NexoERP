"""Complete Catalog Dialog with CRUD operations for products."""

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

from erp.modules.catalog.application.create_product import CreateProductInput
from erp.modules.catalog.application.services import CatalogServices
from erp.modules.catalog.application.update_product import UpdateProductInput
from erp.modules.catalog.domain.product import Product
from erp.modules.catalog.presentation.product_presenter import (
    ProductEditPresenter,
    ProductListPresenter,
)
from erp.shared.application.session import CurrentSession

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class ProductTableModel(QAbstractTableModel):
    """Modelo para a tabela de produtos com suporte a ordenação."""

    def __init__(self, products: list[Product]) -> None:
        super().__init__()
        self._products = products

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        _ = parent
        return len(self._products)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        _ = parent
        return 8

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
            return product.unit
        if column == 3:
            return f"R$ {product.price_cents / 100:.2f}"
        if column == 4:
            return f"R$ {product.cost_cents / 100:.2f}"
        if column == 5:
            return f"{product.margin_pct}%"
        if column == 6:
            return f"{product.stock_qty / 1000:.3f}"
        if column == 7:
            return "Sim" if product.is_low_stock() else "Não"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> object | None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (
                "SKU",
                "Nome",
                "Unidade",
                "Preço",
                "Custo",
                "Margem %",
                "Estoque",
                "Estoque Baixo",
            )[section]
        return None

    def get_product_at(self, row: int) -> Product | None:
        if 0 <= row < len(self._products):
            return self._products[row]
        return None


class ProductEditDialog(QDialog):
    """Diálogo para criar/editar produto."""

    def __init__(
        self,
        presenter: ProductEditPresenter | None,
        session: CurrentSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._session = session
        self._product: Product | None = None

        self.setWindowTitle("Novo Produto")
        self.setModal(True)
        self.resize(500, 500)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._sku_edit = QLineEdit()
        self._sku_edit.setPlaceholderText("Código/SKU único")
        form.addRow("SKU:", self._sku_edit)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Nome do produto")
        form.addRow("Nome:", self._name_edit)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Descrição (opcional)")
        form.addRow("Descrição:", self._desc_edit)

        self._unit_combo = QComboBox()
        self._unit_combo.addItems(["UN", "KG", "L", "M", "M2", "M3", "CX", "PC"])
        self._unit_combo.setEditable(True)
        self._unit_combo.setCurrentText("UN")
        form.addRow("Unidade:", self._unit_combo)

        self._cost_spin = QDoubleSpinBox()
        self._cost_spin.setRange(0.0, 999999.99)
        self._cost_spin.setDecimals(2)
        self._cost_spin.setSuffix(" R$")
        self._cost_spin.setGroupSeparatorShown(True)
        self._cost_spin.setSingleStep(0.01)
        form.addRow("Custo (R$):", self._cost_spin)

        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0.0, 10000.0)
        self._margin_spin.setDecimals(2)
        self._margin_spin.setSuffix(" %")
        self._margin_spin.setGroupSeparatorShown(True)
        self._margin_spin.setSingleStep(0.1)
        self._margin_spin.setValue(30.0)
        form.addRow("Margem (%):", self._margin_spin)

        self._price_spin = QDoubleSpinBox()
        self._price_spin.setRange(0.0, 999999.99)
        self._price_spin.setDecimals(2)
        self._price_spin.setSuffix(" R$")
        self._price_spin.setGroupSeparatorShown(True)
        self._price_spin.setSingleStep(0.01)
        form.addRow("Preço (R$):", self._price_spin)

        # Auto-calculate price from cost + margin
        self._cost_spin.valueChanged.connect(self._on_cost_or_margin_changed)
        self._margin_spin.valueChanged.connect(self._on_cost_or_margin_changed)

        self._min_stock_spin = QSpinBox()
        self._min_stock_spin.setRange(0, 999999)
        self._min_stock_spin.setGroupSeparatorShown(True)
        self._min_stock_spin.setValue(10)
        form.addRow("Estoque mínimo:", self._min_stock_spin)

        self._stock_spin = QSpinBox()
        self._stock_spin.setRange(0, 999999999)
        self._stock_spin.setGroupSeparatorShown(True)
        self._stock_spin.setSuffix(" (em milésimos)")
        form.addRow("Estoque atual:", self._stock_spin)

        self._sold_by_weight_check = QComboBox()
        self._sold_by_weight_check.addItems(["Não (unidade)", "Sim (peso)"])
        form.addRow("Vendido por peso:", self._sold_by_weight_check)

        self._active_check = QComboBox()
        self._active_check.addItems(["Sim", "Não"])
        form.addRow("Ativo:", self._active_check)

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
            price = cost * (1 + margin_pct / 100)
            self._price_spin.setValue(round(price, 2))

    def _on_save_clicked(self) -> None:
        if self._presenter is not None:
            self._presenter.save(
                sku=self._sku_edit.text().strip(),
                name=self._name_edit.text().strip(),
                description=self._desc_edit.text().strip(),
                unit=self._unit_combo.currentText().strip(),
                cost_cents=int(round(self._cost_spin.value() * 100)),
                margin_pct=int(round(self._margin_spin.value() * 100)),  # store as basis points
                price_cents=int(round(self._price_spin.value() * 100)),
                min_stock_qty=self._min_stock_spin.value(),
                stock_qty=self._stock_spin.value() * 1000,  # convert to thousandths
                sold_by_weight=self._sold_by_weight_check.currentIndex() == 1,
                active=self._active_check.currentIndex() == 0,
            )

    # --- ProductEditView implementation ---

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)

    def accept(self) -> None:
        super().accept()

    def load_product(self, product: Product | None) -> None:
        self._product = product
        if product is not None:
            self.setWindowTitle(f"Editar Produto: {product.name}")
            self._sku_edit.setText(product.sku)
            self._sku_edit.setReadOnly(True)
            self._name_edit.setText(product.name)
            self._desc_edit.setText(product.description)
            self._unit_combo.setCurrentText(product.unit)
            self._cost_spin.setValue(product.cost_cents / 100)
            self._margin_spin.setValue(product.margin_pct / 100)
            self._price_spin.setValue(product.price_cents / 100)
            self._min_stock_spin.setValue(product.min_stock_qty)
            self._stock_spin.setValue(product.stock_qty // 1000)
            self._sold_by_weight_check.setCurrentIndex(1 if product.sold_by_weight else 0)
            self._active_check.setCurrentIndex(0 if product.active else 1)
        else:
            self.setWindowTitle("Novo Produto")
            self._sku_edit.setReadOnly(False)


class CatalogWidget(QWidget):
    """Widget principal do catálogo com tabela e ações."""

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

        # Presenters
        self._list_presenter = ProductListPresenter(
            view=self,
            services=services,
            session=session,
        )
        self._edit_presenter = ProductEditPresenter(
            view=self,
            services=services,
            session=session,
        )

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

        self._btn_new = QPushButton("Novo Produto")
        self._btn_new.clicked.connect(self._on_new_product)
        toolbar.addWidget(self._btn_new)

        self._btn_edit = QPushButton("Editar")
        self._btn_edit.clicked.connect(self._on_edit_product)
        self._btn_edit.setEnabled(False)
        toolbar.addWidget(self._btn_edit)

        self._btn_delete = QPushButton("Excluir")
        self._btn_delete.clicked.connect(self._on_delete_product)
        self._btn_delete.setEnabled(False)
        toolbar.addWidget(self._btn_delete)

        self._btn_refresh = QPushButton("Atualizar")
        self._btn_refresh.clicked.connect(self._load_products)
        toolbar.addWidget(self._btn_refresh)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.doubleClicked.connect(self._on_edit_product)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # Proxy model for filtering
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(-1)  # Search all columns
        self._table.setModel(self._proxy_model)

        layout.setContentsMargins(8, 8, 8, 8)

    def _load_products(self) -> None:
        try:
            output = self._services.list_low_stock(company_id=self._session.company_id)
            self._source_model = ProductTableModel(output.products)
            self._proxy_model.setSourceModel(self._source_model)
            self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self._table.horizontalHeader().setStretchLastSection(True)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos: {exc}")

    def _on_search_changed(self, text: str) -> None:
        self._proxy_model.setFilterFixedString(text)

    def _on_selection_changed(self) -> None:
        has_selection = self._table.selectionModel().hasSelection()
        self._btn_edit.setEnabled(has_selection)
        self._btn_delete.setEnabled(has_selection)

    def _on_new_product(self) -> None:
        dialog = ProductEditDialog(None, self._session, self)
        dialog._presenter = self._edit_presenter
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_products()

    def _on_edit_product(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        product = self._source_model.get_product_at(source_index.row())
        if product is None:
            return

        dialog = ProductEditDialog(None, self._session, self)
        dialog._presenter = self._edit_presenter
        dialog.load_product(product)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_products()

    def _on_delete_product(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        product = self._source_model.get_product_at(source_index.row())
        if product is None:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir o produto '{product.name}' (SKU: {product.sku})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._services.delete_product(product.id, company_id=self._session.company_id)
                self._load_products()
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir produto: {exc}")

    # --- ProductListView implementation ---

    def set_products(self, products: list[Product]) -> None:
        self._source_model = ProductTableModel(products)
        self._proxy_model.setSourceModel(self._source_model)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro", message)


def create_catalog_dialog(
    services: CatalogServices,
    session: CurrentSession,
    engine: Engine,
    parent: QWidget | None = None,
) -> QDialog:
    """Factory para criar o diálogo completo de catálogo."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Catálogo de Produtos")
    dialog.resize(900, 600)

    layout = QVBoxLayout(dialog)

    widget = CatalogWidget(services, session, engine, dialog)
    layout.addWidget(widget)

    btn_close = QPushButton("Fechar")
    btn_close.clicked.connect(dialog.accept)
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(btn_close)
    layout.addLayout(btn_layout)

    return dialog