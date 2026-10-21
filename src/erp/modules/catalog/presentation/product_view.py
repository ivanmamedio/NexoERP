"""View for listing products (Qt interface)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from erp.modules.catalog.domain.product import Product
from erp.modules.catalog.presentation.product_presenter import ProductListPresenter


class ProductTableModel(QAbstractTableModel):
    """Modelo simplificado para a tabela de produtos."""

    def __init__(self, products: list[Product]) -> None:
        super().__init__()
        self._products = products

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        _ = parent
        return len(self._products)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        _ = parent
        return 7

    def data(self, index: QModelIndex, role: int) -> object:  # type: ignore[override]
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
            return f"{product.price_cents / 100:.2f}"
        if column == 4:
            return f"{product.cost_cents / 100:.2f}"
        if column == 5:
            return f"{product.stock_qty / 1000:.3f}"
        if column == 6:
            return "Sim" if product.is_low_stock() else "Não"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> object | None:  # type: ignore[override]
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return (
                "SKU",
                "Nome",
                "Unidade",
                "Preço",
                "Custo",
                "Estoque",
                "Estoque Baixo",
            )[section]
        return None


class ProductListWidget(QWidget):
    """Exibe a lista de produtos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: ProductListPresenter | None = None

        self.setWindowTitle("Produtos")
        layout = QVBoxLayout(self)

        self._table = QTableView(self)
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table)

        self._btn_refresh = QPushButton("Atualizar", self)
        self._btn_refresh.clicked.connect(self._on_refresh)
        layout.addWidget(self._btn_refresh)

        layout.setContentsMargins(8, 8, 8, 8)

    def set_presenter(self, presenter: ProductListPresenter) -> None:
        self._presenter = presenter

    def set_products(self, products: list[Product]) -> None:
        self._table.setModel(ProductTableModel(products))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _on_refresh(self) -> None:
        if self._presenter is not None:
            self._presenter.load()
