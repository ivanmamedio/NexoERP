"""Tela de importação de produtos por CSV (Qt)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from erp.modules.import_csv.application.services import ImportProductsServices

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class ImportDialog(QDialog):
    """Diálogo para importação de produtos por CSV."""

    def __init__(
        self,
        services: ImportProductsServices,
        company_id: int,
        user_id: int | None = None,
        username: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._services = services
        self._company_id = company_id
        self._user_id = user_id
        self._username = username
        self._selected_file: str | None = None

        self.setWindowTitle("Importação de Produtos por CSV")
        self.setModal(True)
        self.resize(700, 500)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Instruções
        info = QLabel(
            "Selecione um arquivo CSV para importar produtos. "
            "Colunas obrigatórias: sku, name. "
            "Colunas opcionais: description, unit, cost_cents, margin_pct, "
            "price_cents, min_stock_qty, stock_qty, sold_by_weight, active, "
            "category_name, supplier_name. Preços em centavos, vírgula decimal (pt-BR)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info)

        # Seleção de arquivo
        file_layout = QHBoxLayout()
        self._file_label = QLabel("Nenhum arquivo selecionado")
        self._file_label.setStyleSheet("color: #999; font-style: italic;")
        file_layout.addWidget(self._file_label)

        browse_btn = QPushButton("Selecionar CSV...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # Codificação
        enc_layout = QHBoxLayout()
        enc_layout.addWidget(QLabel("Codificação:"))
        self._encoding_combo = QComboBox()
        self._encoding_combo.addItems(["utf-8", "latin-1", "iso-8859-1", "cp1252"])
        self._encoding_combo.setCurrentText("utf-8")
        enc_layout.addWidget(self._encoding_combo)
        enc_layout.addStretch()
        layout.addLayout(enc_layout)

        # Opção pular linhas inválidas
        self._skip_invalid_cb = QCheckBox("Pular linhas inválidas")
        self._skip_invalid_cb.setChecked(True)
        layout.addWidget(self._skip_invalid_cb)

        # Tabela de pré-visualização/erros
        self._errors_table = QTableWidget(0, 4)
        self._errors_table.setHorizontalHeaderLabels(["Linha", "Campo", "Mensagem", "Valor"])
        self._errors_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._errors_table.setVisible(False)
        layout.addWidget(self._errors_table)

        # Resumo
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #333; font-weight: bold;")
        layout.addWidget(self._summary_label)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._import_btn = QPushButton("Importar")
        self._import_btn.setDefault(True)
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self._import_btn)

        layout.addLayout(btn_layout)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo CSV",
            str(Path.home()),
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_path:
            self._selected_file = file_path
            self._file_label.setText(file_path)
            self._file_label.setStyleSheet("color: #333;")
            self._import_btn.setEnabled(True)
            self._errors_table.setVisible(False)
            self._summary_label.setText("")

    def _on_import(self) -> None:
        if not self._selected_file:
            return

        try:
            output = self._services.import_csv(
                file_path=self._selected_file,
                company_id=self._company_id,
                user_id=self._user_id,
                username=self._username,
                skip_invalid=self._skip_invalid_cb.isChecked(),
                encoding=self._encoding_combo.currentText(),
            )

            result = output.result

            # Atualiza resumo
            summary = (
                f"Importação concluída: {result.imported_count} produto(s) importado(s), "
                f"{result.error_count} erro(s), {result.skipped_count} pulado(s)."
            )
            self._summary_label.setText(summary)
            if result.imported_count > 0:
                self._summary_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif result.error_count > 0:
                self._summary_label.setStyleSheet("color: #c0392b; font-weight: bold;")
            else:
                self._summary_label.setStyleSheet("color: #666; font-weight: bold;")

            # Mostra erros na tabela
            self._errors_table.setRowCount(0)
            if result.errors:
                self._errors_table.setRowCount(len(result.errors))
                for row_idx, error in enumerate(result.errors):
                    self._errors_table.setItem(row_idx, 0, QTableWidgetItem(str(error.line_number)))
                    self._errors_table.setItem(row_idx, 1, QTableWidgetItem(error.field))
                    self._errors_table.setItem(row_idx, 2, QTableWidgetItem(error.message))
                    self._errors_table.setItem(row_idx, 3, QTableWidgetItem(str(error.value)))
                self._errors_table.setVisible(True)

            if result.imported_count > 0:
                QMessageBox.information(
                    self,
                    "Importação Concluída",
                    f"{result.imported_count} produto(s) importado(s) com sucesso.",
                )
                self.accept()
            elif result.error_count > 0:
                QMessageBox.warning(
                    self,
                    "Importação com Erros",
                    "Não foi possível importar nenhum produto devido a erros. "
                    "Veja a tabela de erros acima.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Importação Concluída",
                    "Nenhum produto foi importado.",
                )

        except Exception as exc:  # pragma: no cover - erro inesperado
            QMessageBox.critical(self, "Erro", f"Erro ao importar CSV: {exc}")


def create_import_dialog(
    services: ImportProductsServices,
    company_id: int,
    user_id: int | None = None,
    username: str = "",
    parent: QWidget | None = None,
) -> ImportDialog:
    """Factory para criar o diálogo de importação."""
    return ImportDialog(
        services=services,
        company_id=company_id,
        user_id=user_id,
        username=username,
        parent=parent,
    )
