"""Graphical reports dialog for visual analytics."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from erp.modules.reports.application.service import ReportService
    from sqlalchemy.orm import Session


class GraphicalReportCanvas(FigureCanvas):
    """Canvas para renderizar gráficos matplotlib no Qt."""

    def __init__(self, parent: QWidget | None = None, width: int = 8, height: int = 6, dpi: int = 100):
        self._figure = Figure(figsize=(width, height), dpi=dpi)
        self._axes = self._figure.add_subplot(111)
        super().__init__(self._figure)
        self.setParent(parent)
        self._figure.tight_layout()

    @property
    def axes(self):
        return self._axes

    @property
    def figure(self):
        return self._figure

    def clear_plot(self) -> None:
        self._axes.clear()
        self._figure.tight_layout()
        self.draw()

    def plot_line_chart(self, x_data, y_data, x_label: str, y_label: str, title: str) -> None:
        self._axes.clear()
        self._axes.plot(x_data, y_data, marker='o', linewidth=2, markersize=6, color='#2980b9')
        self._axes.set_xlabel(x_label)
        self._axes.set_ylabel(y_label)
        self._axes.set_title(title)
        self._axes.grid(True, alpha=0.3)
        self._figure.autofmt_xdate(rotation=45)
        self._figure.tight_layout()
        self.draw()

    def plot_bar_chart(self, x_labels, y_data, x_label: str, y_label: str, title: str, horizontal: bool = False) -> None:
        self._axes.clear()
        if horizontal:
            bars = self._axes.barh(range(len(x_labels)), y_data, color='#27ae60', alpha=0.8)
            self._axes.set_yticks(range(len(x_labels)))
            self._axes.set_yticklabels(x_labels)
            self._axes.set_xlabel(y_label)
            self._axes.set_ylabel(x_label)
            # Add value labels
            for i, (bar, val) in enumerate(zip(bars, y_data)):
                self._axes.text(bar.get_width() + max(y_data) * 0.01, bar.get_y() + bar.get_height()/2, 
                              f'R$ {val:,.2f}', va='center', fontsize=9)
        else:
            bars = self._axes.bar(range(len(x_labels)), y_data, color='#27ae60', alpha=0.8)
            self._axes.set_xticks(range(len(x_labels)))
            self._axes.set_xticklabels(x_labels, rotation=45, ha='right')
            self._axes.set_xlabel(x_label)
            self._axes.set_ylabel(y_label)
            # Add value labels
            for bar, val in zip(bars, y_data):
                self._axes.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(y_data) * 0.01, 
                              f'R$ {val:,.2f}', ha='center', va='bottom', fontsize=9)
        self._axes.set_title(title)
        self._axes.grid(True, alpha=0.3, axis='y' if horizontal else 'x')
        self._figure.tight_layout()
        self.draw()

    def plot_grouped_bar_chart(self, x_labels, series_data: dict, x_label: str, y_label: str, title: str) -> None:
        """series_data: dict com nome da série -> lista de valores."""
        self._axes.clear()
        x = range(len(x_labels))
        width = 0.8 / len(series_data)
        colors = ['#2980b9', '#c0392b', '#27ae60', '#f39c12', '#8e44ad']
        
        for i, (series_name, values) in enumerate(series_data.items()):
            offset = (i - len(series_data) / 2 + 0.5) * width
            bars = self._axes.bar([xi + offset for xi in x], values, width, label=series_name, 
                                color=colors[i % len(colors)], alpha=0.8)
            # Add value labels
            for bar, val in zip(bars, values):
                if val > 0:
                    self._axes.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values) * 0.01, 
                                  f'R$ {val:,.0f}', ha='center', va='bottom', fontsize=8)
        
        self._axes.set_xticks(x)
        self._axes.set_xticklabels(x_labels, rotation=45, ha='right')
        self._axes.set_xlabel(x_label)
        self._axes.set_ylabel(y_label)
        self._axes.set_title(title)
        self._axes.legend()
        self._axes.grid(True, alpha=0.3, axis='y')
        self._figure.tight_layout()
        self.draw()

    def plot_pie_chart(self, labels, values, title: str) -> None:
        self._axes.clear()
        colors = ['#2980b9', '#c0392b', '#27ae60', '#f39c12', '#8e44ad', '#e74c3c', '#34495e', '#16a085']
        wedges, texts, autotexts = self._axes.pie(values, labels=labels, autopct='%1.1f%%', 
                                                   colors=colors, startangle=90)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        self._axes.set_title(title)
        self._figure.tight_layout()
        self.draw()


class GraphicalReportsDialog(QDialog):
    """Dialog para relatórios gráficos."""

    def __init__(
        self,
        report_service: ReportService,
        company_id: int,
        session_factory: callable,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._report_service = report_service
        self._company_id = company_id
        self._session_factory = session_factory

        self.setWindowTitle("Relatórios Gráficos - Análise Visual")
        self.setModal(True)
        self.resize(1200, 800)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Controles superiores
        controls_layout = QHBoxLayout()

        # Tipo de relatório
        controls_layout.addWidget(QLabel("Relatório:"))
        self._report_combo = QComboBox()
        self._report_combo.addItems([
            "Faturamento por Período",
            "Ranking Produtos Mais Vendidos",
            "Receita x Custo x Lucro",
            "Vendas por Forma de Pagamento",
        ])
        self._report_combo.setMinimumWidth(250)
        controls_layout.addWidget(self._report_combo)

        # Período
        controls_layout.addWidget(QLabel("Período:"))
        self._period_combo = QComboBox()
        self._period_combo.addItems(["Hoje", "7 dias", "30 dias", "Personalizado"])
        self._period_combo.currentTextChanged.connect(self._on_period_changed)
        controls_layout.addWidget(self._period_combo)

        # Data inicial (para personalizado)
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate().addDays(-30))
        self._start_date.setEnabled(False)
        self._start_date.setMinimumWidth(120)
        controls_layout.addWidget(QLabel("Início:"))
        controls_layout.addWidget(self._start_date)

        # Data final (para personalizado)
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._end_date.setEnabled(False)
        self._end_date.setMinimumWidth(120)
        controls_layout.addWidget(QLabel("Fim:"))
        controls_layout.addWidget(self._end_date)

        controls_layout.addStretch()

        # Tipo de gráfico
        controls_layout.addWidget(QLabel("Visualização:"))
        self._chart_type_combo = QComboBox()
        self._chart_type_combo.addItems([
            "Linha (Temporal)",
            "Barras Verticais",
            "Barras Horizontais",
            "Colunas Comparativas",
            "Pizza / Rosca",
        ])
        controls_layout.addWidget(self._chart_type_combo)

        # Botão gerar
        generate_btn = QPushButton("Gerar Gráfico")
        generate_btn.setDefault(True)
        generate_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        generate_btn.clicked.connect(self._on_generate)
        controls_layout.addWidget(generate_btn)

        layout.addLayout(controls_layout)

        # Separator
        from PySide6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Área do gráfico
        self._canvas = GraphicalReportCanvas(self, width=10, height=7)
        self._toolbar = NavigationToolbar(self._canvas, self)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas, 1)

        # Status label
        self._status_label = QLabel("Selecione um relatório e clique em 'Gerar Gráfico'")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: #7f8c8d; padding: 10px;")
        layout.addWidget(self._status_label)

    def _on_period_changed(self, text: str) -> None:
        is_custom = text == "Personalizado"
        self._start_date.setEnabled(is_custom)
        self._end_date.setEnabled(is_custom)
        if not is_custom:
            days_map = {"Hoje": 0, "7 dias": 7, "30 dias": 30}
            days = days_map.get(text, 30)
            from PySide6.QtCore import QDate
            self._end_date.setDate(QDate.currentDate())
            self._start_date.setDate(QDate.currentDate().addDays(-days))

    def _get_date_range(self) -> tuple[datetime, datetime]:
        """Retorna (start_date, end_date) baseado no período selecionado."""
        period = self._period_combo.currentText()
        now = datetime.now(UTC)
        
        if period == "Hoje":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "7 dias":
            start = (now.replace(hour=0, minute=0, second=0, microsecond=0))
            start = start.replace(day=start.day - 7)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "30 dias":
            start = (now.replace(hour=0, minute=0, second=0, microsecond=0))
            start = start.replace(day=start.day - 30)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:  # Personalizado
            from PySide6.QtCore import QDate
            start_qdate = self._start_date.date()
            end_qdate = self._end_date.date()
            start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day(), tzinfo=UTC)
            end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59, tzinfo=UTC)
        
        return start, end

    def _on_generate(self) -> None:
        report_type = self._report_combo.currentText()
        chart_type = self._chart_type_combo.currentText()
        start_date, end_date = self._get_date_range()

        try:
            self._status_label.setText(f"Gerando {report_type}...")
            QApplication.processEvents()

            if report_type == "Faturamento por Período":
                self._generate_revenue_chart(chart_type, start_date, end_date)
            elif report_type == "Ranking Produtos Mais Vendidos":
                self._generate_top_products_chart(chart_type, start_date, end_date)
            elif report_type == "Receita x Custo x Lucro":
                self._generate_profit_chart(chart_type, start_date, end_date)
            elif report_type == "Vendas por Forma de Pagamento":
                self._generate_payment_chart(chart_type, start_date, end_date)
            else:
                QMessageBox.warning(self, "Aviso", "Tipo de relatório não implementado.")
                return

            self._status_label.setText(f"Gráfico gerado: {report_type} - {chart_type}")

        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico: {exc}")
            self._status_label.setText("Erro ao gerar gráfico")

    def _generate_revenue_chart(self, chart_type: str, start_date: datetime, end_date: datetime) -> None:
        """Gráfico de faturamento por período."""
        with self._session_factory() as session:
            from sqlalchemy import text
            sql = """
                SELECT date(s.created_at) as sale_date, COALESCE(SUM(s.total_cents), 0) as total_sales
                FROM sales s
                WHERE s.company_id = :company_id
                AND s.status = 'finalized'
                AND s.created_at >= :start_date
                AND s.created_at <= :end_date
                GROUP BY date(s.created_at)
                ORDER BY sale_date
            """
            params = {"company_id": self._company_id, "start_date": start_date, "end_date": end_date}
            result = session.execute(text(sql), params)
            rows = result.fetchall()

        if not rows:
            self._canvas.clear_plot()
            self._canvas.axes.text(0.5, 0.5, 'Sem dados no período', ha='center', va='center', transform=self._canvas.axes.transAxes)
            self._canvas.draw()
            return

        dates = [row.sale_date for row in rows]
        values = [float(row.total_sales) / 100 for row in rows]  # converter centavos para reais

        if "Linha" in self._chart_type_combo.currentText():
            self._canvas.plot_line_chart(dates, values, "Data", "Faturamento (R$)", "Faturamento por Período")
        elif "Barras Verticais" in self._chart_type_combo.currentText():
            date_strs = [d.strftime("%d/%m") for d in dates]
            self._canvas.plot_bar_chart(date_strs, values, "Data", "Faturamento (R$)", "Faturamento por Período")
        elif "Barras Horizontais" in self._chart_type_combo.currentText():
            date_strs = [d.strftime("%d/%m") for d in dates]
            self._canvas.plot_bar_chart(date_strs, values, "Faturamento (R$)", "Data", "Faturamento por Período", horizontal=True)
        elif "Colunas" in self._chart_type_combo.currentText():
            date_strs = [d.strftime("%d/%m") for d in dates]
            self._canvas.plot_bar_chart(date_strs, values, "Data", "Faturamento (R$)", "Faturamento por Período")
        else:  # Pizza
            # Para pizza, agrupar por semana/mês
            self._canvas.plot_pie_chart([d.strftime("%d/%m") for d in dates[-7:]], values[-7:], "Faturamento - Últimos 7 dias")

    def _generate_top_products_chart(self, chart_type: str, start_date: datetime, end_date: datetime) -> None:
        """Ranking de produtos mais vendidos."""
        with self._session_factory() as session:
            from sqlalchemy import text
            sql = """
                SELECT p.name, COALESCE(SUM(si.quantity_thousandths), 0) as qty, COALESCE(SUM(si.line_total_cents), 0) as revenue
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE s.company_id = :company_id
                AND s.status = 'finalized'
                AND s.created_at >= :start_date
                AND s.created_at <= :end_date
                GROUP BY p.id, p.name
                ORDER BY revenue DESC
                LIMIT 10
            """
            params = {"company_id": self._company_id, "start_date": start_date, "end_date": end_date}
            result = session.execute(text(sql), params)
            rows = result.fetchall()

        if not rows:
            self._canvas.clear_plot()
            self._canvas.axes.text(0.5, 0.5, 'Sem dados no período', ha='center', va='center', transform=self._canvas.axes.transAxes)
            self._canvas.draw()
            return

        names = [row.name[:30] for row in rows]  # truncar nomes longos
        quantities = [float(row.qty) / 1000 for row in rows]  # milésimos para unidades
        revenues = [float(row.revenue) / 100 for row in rows]

        if "Horizontais" in self._chart_type_combo.currentText():
            self._canvas.plot_bar_chart(names, revenues, "Receita (R$)", "Produto", "Top 10 Produtos por Receita", horizontal=True)
        elif "Pizza" in self._chart_type_combo.currentText():
            self._canvas.plot_pie_chart(names, revenues, "Participação na Receita - Top 10")
        else:
            self._canvas.plot_bar_chart(names, revenues, "Produto", "Receita (R$)", "Top 10 Produtos por Receita")

    def _generate_profit_chart(self, chart_type: str, start_date: datetime, end_date: datetime) -> None:
        """Receita x Custo x Lucro."""
        with self._session_factory() as session:
            from sqlalchemy import text
            # Receita
            rev_sql = """
                SELECT COALESCE(SUM(s.total_cents), 0) as revenue
                FROM sales s
                WHERE s.company_id = :company_id AND s.status = 'finalized'
                AND s.created_at >= :start_date AND s.created_at <= :end_date
            """
            rev_result = session.execute(text(rev_sql), {"company_id": self._company_id, "start_date": start_date, "end_date": end_date})
            revenue = float(rev_result.scalar() or 0) / 100

            # Custo dos produtos vendidos
            cost_sql = """
                SELECT COALESCE(SUM(si.quantity_thousandths * p.cost_cents / 1000), 0) as total_cost
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE s.company_id = :company_id AND s.status = 'finalized'
                AND s.created_at >= :start_date AND s.created_at <= :end_date
            """
            cost_result = session.execute(text(cost_sql), {"company_id": self._company_id, "start_date": start_date, "end_date": end_date})
            total_cost = float(cost_result.scalar() or 0) / 100

        profit = revenue - total_cost

        categories = ["Receita", "Custo", "Lucro"]
        values = [revenue, total_cost, profit]

        if "Pizza" in self._chart_type_combo.currentText():
            self._canvas.plot_pie_chart(categories, [abs(v) for v in values], "Distribuição Receita/Custo/Lucro")
        else:
            self._canvas.plot_bar_chart(categories, values, "Categoria", "Valor (R$)", "Receita x Custo x Lucro")

    def _generate_payment_chart(self, chart_type: str, start_date: datetime, end_date: datetime) -> None:
        """Vendas por forma de pagamento."""
        with self._session_factory() as session:
            from sqlalchemy import text
            sql = """
                SELECT sp.method, COALESCE(SUM(sp.amount_cents), 0) as amount
                FROM sale_payments sp
                JOIN sales s ON sp.sale_id = s.id
                WHERE s.company_id = :company_id AND s.status = 'finalized'
                AND s.created_at >= :start_date AND s.created_at <= :end_date
                GROUP BY sp.method
                ORDER BY amount DESC
            """
            params = {"company_id": self._company_id, "start_date": start_date, "end_date": end_date}
            result = session.execute(text(sql), params)
            rows = result.fetchall()

        if not rows:
            self._canvas.clear_plot()
            self._canvas.axes.text(0.5, 0.5, 'Sem dados no período', ha='center', va='center', transform=self._canvas.axes.transAxes)
            self._canvas.draw()
            return

        methods = [row.method for row in rows]
        values = [float(row.amount) / 100 for row in rows]

        if "Pizza" in self._chart_type_combo.currentText():
            self._canvas.plot_pie_chart(methods, values, "Vendas por Forma de Pagamento")
        elif "Horizontais" in self._chart_type_combo.currentText():
            self._canvas.plot_bar_chart(methods, values, "Valor (R$)", "Forma de Pagamento", "Vendas por Forma de Pagamento", horizontal=True)
        else:
            self._canvas.plot_bar_chart(methods, values, "Forma de Pagamento", "Valor (R$)", "Vendas por Forma de Pagamento")


def create_graphical_reports_dialog(
    report_service: ReportService,
    company_id: int,
    session_factory: callable,
    parent: QWidget | None = None,
) -> QDialog:
    """Factory para criar o diálogo de relatórios gráficos."""
    return GraphicalReportsDialog(report_service, company_id, session_factory, parent)