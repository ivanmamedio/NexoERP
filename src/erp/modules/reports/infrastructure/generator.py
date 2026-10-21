"""SQL-based report generator using raw queries for performance."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.orm import Session

from erp.modules.reports.application.ports import ReportGeneratorPort
from erp.modules.reports.domain import (
    CashClosingRow,
    LowStockRow,
    ProfitMarginRow,
    ReportFilter,
    SalesByOperatorRow,
    SalesByPeriodRow,
    SalesByProductRow,
    SimpleDRERow,
)

if TYPE_CHECKING:
    pass


class SqlReportGenerator(ReportGeneratorPort):
    """Report generator using raw SQL queries for performance."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def generate_sales_by_period(self, filter_: ReportFilter) -> list[SalesByPeriodRow]:
        sql = """
            SELECT
                date(s.created_at) as sale_date,
                COALESCE(SUM(s.total_amount), 0) as total_sales,
                COALESCE(SUM(si.quantity), 0) as total_items,
                COUNT(DISTINCT s.id) as total_transactions
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            WHERE s.company_id = :company_id
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.start_date:
            sql += " AND s.created_at >= :start_date"
            params["start_date"] = filter_.start_date
        if filter_.end_date:
            sql += " AND s.created_at <= :end_date"
            params["end_date"] = filter_.end_date
        if filter_.operator_id:
            sql += " AND s.operator_id = :operator_id"
            params["operator_id"] = filter_.operator_id

        sql += " GROUP BY date(s.created_at) ORDER BY sale_date"

        result = self._session.execute(text(sql), params)
        rows = []
        for row in result:
            rows.append(
                SalesByPeriodRow(
                    date=row.sale_date,
                    total_sales=Decimal(str(row.total_sales or 0)),
                    total_items=int(row.total_items or 0),
                    total_transactions=int(row.total_transactions or 0),
                )
            )
        return rows

    def generate_sales_by_product(self, filter_: ReportFilter) -> list[SalesByProductRow]:
        sql = """
            SELECT
                p.id as product_id,
                p.name as product_name,
                p.sku,
                COALESCE(SUM(si.quantity), 0) as quantity_sold,
                COALESCE(SUM(si.total_price), 0) as total_revenue,
                CASE WHEN SUM(si.quantity) > 0
                    THEN SUM(si.total_price) / SUM(si.quantity)
                    ELSE 0 END as avg_price
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE s.company_id = :company_id
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.start_date:
            sql += " AND s.created_at >= :start_date"
            params["start_date"] = filter_.start_date
        if filter_.end_date:
            sql += " AND s.created_at <= :end_date"
            params["end_date"] = filter_.end_date
        if filter_.operator_id:
            sql += " AND s.operator_id = :operator_id"
            params["operator_id"] = filter_.operator_id
        if filter_.category_id:
            sql += " AND p.category_id = :category_id"
            params["category_id"] = filter_.category_id
        if filter_.product_id:
            sql += " AND p.id = :product_id"
            params["product_id"] = filter_.product_id

        sql += " GROUP BY p.id, p.name, p.sku ORDER BY total_revenue DESC"

        result = self._session.execute(text(sql), params)
        rows = []
        for row in result:
            rows.append(
                SalesByProductRow(
                    product_id=row.product_id,
                    product_name=row.product_name,
                    sku=row.sku,
                    quantity_sold=int(row.quantity_sold or 0),
                    total_revenue=Decimal(str(row.total_revenue or 0)),
                    avg_price=Decimal(str(row.avg_price or 0)),
                )
            )
        return rows

    def generate_sales_by_operator(self, filter_: ReportFilter) -> list[SalesByOperatorRow]:
        sql = """
            SELECT
                u.id as operator_id,
                u.name as operator_name,
                COALESCE(SUM(s.total_amount), 0) as total_sales,
                COUNT(DISTINCT s.id) as total_transactions,
                CASE WHEN COUNT(DISTINCT s.id) > 0
                    THEN SUM(s.total_amount) / COUNT(DISTINCT s.id)
                    ELSE 0 END as avg_ticket
            FROM sales s
            JOIN users u ON s.operator_id = u.id
            WHERE s.company_id = :company_id
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.start_date:
            sql += " AND s.created_at >= :start_date"
            params["start_date"] = filter_.start_date
        if filter_.end_date:
            sql += " AND s.created_at <= :end_date"
            params["end_date"] = filter_.end_date
        if filter_.operator_id:
            sql += " AND u.id = :operator_id"
            params["operator_id"] = filter_.operator_id

        sql += " GROUP BY u.id, u.name ORDER BY total_sales DESC"

        result = self._session.execute(text(sql), params)
        rows = []
        for row in result:
            rows.append(
                SalesByOperatorRow(
                    operator_id=row.operator_id,
                    operator_name=row.operator_name,
                    total_sales=Decimal(str(row.total_sales or 0)),
                    total_transactions=int(row.total_transactions or 0),
                    avg_ticket=Decimal(str(row.avg_ticket or 0)),
                )
            )
        return rows

    def generate_low_stock(self, filter_: ReportFilter) -> list[LowStockRow]:
        sql = """
            SELECT
                p.id as product_id,
                p.name as product_name,
                p.sku,
                COALESCE(i.quantity, 0) as current_stock,
                p.min_stock,
                c.name as category_name
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id AND i.company_id = :company_id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.company_id = :company_id
            AND p.active = 1
            AND p.min_stock > 0
            AND COALESCE(i.quantity, 0) <= p.min_stock
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.category_id:
            sql += " AND p.category_id = :category_id"
            params["category_id"] = filter_.category_id
        if filter_.product_id:
            sql += " AND p.id = :product_id"
            params["product_id"] = filter_.product_id

        sql += " ORDER BY current_stock ASC, p.name"

        result = self._session.execute(text(sql), params)
        rows = []
        for row in result:
            rows.append(
                LowStockRow(
                    product_id=row.product_id,
                    product_name=row.product_name,
                    sku=row.sku,
                    current_stock=int(row.current_stock or 0),
                    min_stock=int(row.min_stock or 0),
                    category_name=row.category_name or "",
                )
            )
        return rows

    def generate_profit_margin(self, filter_: ReportFilter) -> list[ProfitMarginRow]:
        sql = """
            SELECT
                p.id as product_id,
                p.name as product_name,
                p.sku,
                p.cost_price,
                p.sale_price,
                (p.sale_price - p.cost_price) as margin_amount,
                CASE WHEN p.sale_price > 0
                    THEN ((p.sale_price - p.cost_price) / p.sale_price) * 100
                    ELSE 0 END as margin_percent
            FROM products p
            WHERE p.company_id = :company_id
            AND p.active = 1
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.category_id:
            sql += " AND p.category_id = :category_id"
            params["category_id"] = filter_.category_id
        if filter_.product_id:
            sql += " AND p.id = :product_id"
            params["product_id"] = filter_.product_id

        sql += " ORDER BY margin_percent DESC"

        result = self._session.execute(text(sql), params)
        rows = []
        for row in result:
            rows.append(
                ProfitMarginRow(
                    product_id=row.product_id,
                    product_name=row.product_name,
                    sku=row.sku,
                    cost_price=Decimal(str(row.cost_price or 0)),
                    sale_price=Decimal(str(row.sale_price or 0)),
                    margin_amount=Decimal(str(row.margin_amount or 0)),
                    margin_percent=Decimal(str(row.margin_percent or 0)),
                )
            )
        return rows

    def generate_simple_dre(self, filter_: ReportFilter) -> list[SimpleDRERow]:
        # Revenue
        revenue_sql = """
            SELECT
                'receita' as category,
                'Vendas' as description,
                COALESCE(SUM(s.total_amount), 0) as amount
            FROM sales s
            WHERE s.company_id = :company_id
            AND s.status = 'finalized'
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.start_date:
            revenue_sql += " AND s.created_at >= :start_date"
            params["start_date"] = filter_.start_date
        if filter_.end_date:
            revenue_sql += " AND s.created_at <= :end_date"
            params["end_date"] = filter_.end_date

        revenue_result = self._session.execute(text(revenue_sql), params)
        rows = []
        for row in revenue_result:
            rows.append(
                SimpleDRERow(
                    category=row.category,
                    description=row.description,
                    amount=Decimal(str(row.amount or 0)),
                )
            )

        # Expenses (from treasury payables)
        expense_sql = """
            SELECT
                'despesa' as category,
                fc.name as description,
                COALESCE(SUM(pi.amount), 0) as amount
            FROM payable_installments pi
            JOIN payables p ON pi.payable_id = p.id
            JOIN financial_categories fc ON p.category_id = fc.id
            WHERE p.company_id = :company_id
            AND p.status = 'paid'
        """
        if filter_.start_date:
            expense_sql += " AND pi.due_date >= :start_date"
        if filter_.end_date:
            expense_sql += " AND pi.due_date <= :end_date"

        expense_sql += " GROUP BY fc.id, fc.name ORDER BY amount DESC"

        expense_result = self._session.execute(text(expense_sql), params)
        for row in expense_result:
            rows.append(
                SimpleDRERow(
                    category=row.category,
                    description=row.description,
                    amount=Decimal(str(row.amount or 0)),
                )
            )

        # Calculate profit
        total_revenue = sum(r.amount for r in rows if r.category == "receita")
        total_expenses = sum(r.amount for r in rows if r.category == "despesa")
        profit = Decimal(str(total_revenue - total_expenses))

        rows.append(
            SimpleDRERow(
                category="lucro",
                description="Lucro Líquido",
                amount=profit,
            )
        )

        return rows

    def generate_cash_closing(self, filter_: ReportFilter) -> list[CashClosingRow]:
        sql = """
            SELECT
                cs.id as session_id,
                cs.opened_at,
                cs.closed_at,
                u.name as operator_name,
                cs.opening_amount,
                cs.expected_amount,
                cs.closing_amount as actual_amount,
                COALESCE(cs.closing_amount, 0) - COALESCE(cs.expected_amount, 0) as difference,
                COALESCE((
                    SELECT SUM(amount) FROM cash_movements
                    WHERE session_id = cs.id AND type = 'sangria'
                ), 0) as sangrias,
                COALESCE((
                    SELECT SUM(amount) FROM cash_movements
                    WHERE session_id = cs.id AND type = 'suprimento'
                ), 0) as suprimentos
            FROM cash_sessions cs
            JOIN users u ON cs.operator_id = u.id
            WHERE cs.company_id = :company_id
        """
        params: dict[str, object] = {"company_id": filter_.company_id}

        if filter_.start_date:
            sql += " AND cs.opened_at >= :start_date"
            params["start_date"] = filter_.start_date
        if filter_.end_date:
            sql += " AND cs.opened_at <= :end_date"
            params["end_date"] = filter_.end_date
        if filter_.operator_id:
            sql += " AND cs.operator_id = :operator_id"
            params["operator_id"] = filter_.operator_id

        sql += " ORDER BY cs.opened_at DESC"

        result = self._session.execute(text(sql), params)
        rows = []
        for row in result:
            rows.append(
                CashClosingRow(
                    session_id=row.session_id,
                    opened_at=row.opened_at,
                    closed_at=row.closed_at,
                    operator_name=row.operator_name,
                    opening_amount=Decimal(str(row.opening_amount or 0)),
                    expected_amount=Decimal(str(row.expected_amount or 0)),
                    actual_amount=Decimal(str(row.actual_amount or 0)),
                    difference=Decimal(str(row.difference or 0)),
                    sangrias=Decimal(str(row.sangrias or 0)),
                    suprimentos=Decimal(str(row.suprimentos or 0)),
                )
            )
        return rows
