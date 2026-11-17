#!/usr/bin/env python3
"""Script de carga para Task 5.1 — gera 50k produtos e 100k vendas, mede performance.

Uso:
    uv run python scripts/load_test.py --seed
    uv run python scripts/load_test.py --measure
    uv run python scripts/load_test.py --seed --measure
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from erp.bootstrap import bootstrap
from erp.modules.catalog.domain.product import Product
from erp.modules.catalog.infrastructure.models import ProductModel
from erp.modules.sales.domain.sale import Sale
from erp.modules.sales.domain.sale_item import SaleItem
from erp.modules.sales.domain.sale_payment import SalePayment
from erp.modules.sales.infrastructure.models import SaleItemModel, SaleModel, SalePaymentModel
from erp.modules.treasury.domain.financial_category import FinancialCategory
from erp.modules.treasury.infrastructure.models import FinancialCategoryModel
from erp.modules.cash.domain.cash_session import CashSession
from erp.modules.cash.infrastructure.models import CashRegisterModel, CashSessionModel
from erp.modules.identity.infrastructure.models import UserModel
from erp.shared.application.session import CurrentSession
from erp.shared.domain.value_objects import Money


@dataclass
class LoadTestConfig:
    num_products: int = 50_000
    num_sales: int = 100_000
    num_categories: int = 20
    num_suppliers: int = 50
    num_cash_registers: int = 4
    num_users: int = 10
    batch_size: int = 1_000


class LoadTester:
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.ctx = bootstrap()
        self.engine = self.ctx.engine
        self.company_id = 1  # empresa padrão

    def _get_session(self) -> Session:
        return Session(self.engine)

    def seed_all(self) -> None:
        """Executa todo o seeding: categorias, fornecedores, produtos, vendas."""
        print("=" * 60)
        print("INICIANDO SEED DE CARGA (50k produtos, 100k vendas)")
        print("=" * 60)

        start = time.perf_counter()

        with self._get_session() as session:
            self._ensure_company(session)
            self._ensure_users(session)
            self._ensure_categories(session)
            self._ensure_suppliers(session)
            self._ensure_cash_registers(session)
            self._ensure_financial_categories(session)
            session.commit()

        self._seed_products()
        self._seed_sales()
        self._seed_cash_sessions()

        elapsed = time.perf_counter() - start
        print(f"\n✅ Seed completo em {elapsed:.2f}s")

    def _ensure_company(self, session: Session) -> None:
        # Verifica se empresa 1 existe
        result = session.execute(text("SELECT 1 FROM companies WHERE id = 1")).fetchone()
        if not result:
            now = datetime.now(UTC)
            session.execute(text("""
                INSERT INTO companies (id, company_id, name, trade_name, tax_id, address, phone, email, active, created_at, updated_at)
                VALUES (1, 1, 'Empresa Teste', 'Empresa Teste', '00.000.000/0001-00', 'Rua Teste, 123', '(11) 99999-9999', 'teste@empresa.com', 1, :now, :now)
            """), {"now": now})
            print("  📦 Empresa 1 criada")

    def _ensure_users(self, session: Session) -> None:
        # Verifica usuários
        count = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if count >= self.config.num_users:
            print(f"  👥 {count} usuários já existem")
            return

        # Cria usuários adicionais
        from erp.modules.identity.infrastructure.hasher import BcryptHasher
        hasher = BcryptHasher()

        for i in range(count + 1, self.config.num_users + 1):
            user_number = i - 1  # admin é 0
            employee_name = f"Operador {i}"
            password_hash = hasher.hash("senha123")
            session.execute(text("""
                INSERT INTO users (user_number, employee_name, password_hash, must_change_password,
                                 failed_login_attempts, locked_until, is_active, company_id,
                                 created_at, updated_at)
                VALUES (:user_number, :employee_name, :password_hash, 0, 0, NULL, 1, 1, :now, :now)
            """), {
                "user_number": user_number,
                "employee_name": employee_name,
                "password_hash": password_hash,
                "now": datetime.now(UTC),
            })

            # Atribui papel de Caixa
            session.execute(text("""
                INSERT INTO user_company_roles (user_id, role_id, company_id)
                SELECT u.id, r.id, 1 FROM users u, roles r
                WHERE u.user_number = :user_number AND r.name = 'Caixa'
            """), {"user_number": user_number})

        session.commit()
        print(f"  👥 {self.config.num_users} usuários garantidos")

    def _ensure_categories(self, session: Session) -> None:
        count = session.execute(text("SELECT COUNT(*) FROM categories WHERE company_id = 1")).scalar()
        if count >= self.config.num_categories:
            print(f"  📂 {count} categorias já existem")
            return

        for i in range(count + 1, self.config.num_categories + 1):
            session.execute(text("""
                INSERT INTO categories (company_id, name, description, parent_id, is_active, created_at, updated_at)
                VALUES (1, :name, :description, NULL, 1, :now, :now)
            """), {"name": f"Categoria {i}", "description": f"Descrição da categoria {i}", "now": datetime.now(UTC)})

        session.commit()
        print(f"  📂 {self.config.num_categories} categorias garantidas")

    def _ensure_suppliers(self, session: Session) -> None:
        count = session.execute(text("SELECT COUNT(*) FROM suppliers WHERE company_id = 1")).scalar()
        if count >= self.config.num_suppliers:
            print(f"  🚚 {count} fornecedores já existem")
            return

        for i in range(count + 1, self.config.num_suppliers + 1):
            session.execute(text("""
                INSERT INTO suppliers (company_id, name, trade_name, tax_id, contact_name, phone, email, is_active, created_at, updated_at)
                VALUES (1, :name, :trade_name, :tax_id, :contact_name, :phone, :email, 1, :now, :now)
            """), {
                "name": f"Fornecedor {i}",
                "trade_name": f"Fornecedor {i} Ltda",
                "tax_id": f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99):02d}",
                "contact_name": f"Contato {i}",
                "phone": f"(11) 9{random.randint(1000,9999)}-{random.randint(1000,9999):04d}",
                "email": f"contato{i}@fornecedor{i}.com",
                "now": datetime.now(UTC),
            })

        session.commit()
        print(f"  🚚 {self.config.num_suppliers} fornecedores garantidos")

    def _ensure_cash_registers(self, session: Session) -> None:
        count = session.execute(text("SELECT COUNT(*) FROM cash_registers WHERE company_id = 1")).scalar()
        if count >= self.config.num_cash_registers:
            print(f"  💰 {count} caixas já existem")
            return

        for i in range(count + 1, self.config.num_cash_registers + 1):
            session.execute(text("""
                INSERT INTO cash_registers (company_id, name, terminal_code, active, created_at, updated_at)
                VALUES (1, :name, :terminal_code, 1, :now, :now)
            """), {"name": f"Caixa {i}", "terminal_code": f"TERM{i:03d}", "now": datetime.now(UTC)})

        session.commit()
        print(f"  💰 {self.config.num_cash_registers} caixas garantidos")

    def _ensure_financial_categories(self, session: Session) -> None:
        count = session.execute(text("SELECT COUNT(*) FROM financial_categories WHERE company_id = 1")).scalar()
        if count >= 10:
            print(f"  💳 {count} categorias financeiras já existem")
            return

        categories = [
            ("Receita", "Vendas", "income", "Receitas de vendas"),
            ("Receita", "Serviços", "income", "Receitas de serviços"),
            ("Despesa", "Mercadorias", "expense", "Compra de mercadorias"),
            ("Despesa", "Aluguel", "expense", "Aluguel do imóvel"),
            ("Despesa", "Salários", "expense", "Pagamento de salários"),
            ("Despesa", "Impostos", "expense", "Pagamento de impostos"),
            ("Despesa", "Marketing", "expense", "Marketing e publicidade"),
            ("Transferência", "Banco", "transfer", "Transferências bancárias"),
        ]

        for kind, name, cat_kind, description in categories:
            session.execute(text("""
                INSERT INTO financial_categories (company_id, name, kind, description, is_active, created_at, updated_at)
                VALUES (1, :name, :kind, :description, 1, :now, :now)
            """), {"name": name, "kind": cat_kind, "description": description, "now": datetime.now(UTC)})

        session.commit()
        print(f"  💳 Categorias financeiras garantidas")

    def _seed_products(self) -> None:
        print(f"\n  📦 Criando {self.config.num_products} produtos...")

        # Busca IDs necessários
        with self._get_session() as session:
            category_ids = [row[0] for row in session.execute(text("SELECT id FROM categories WHERE company_id = 1")).fetchall()]
            supplier_ids = [row[0] for row in session.execute(text("SELECT id FROM suppliers WHERE company_id = 1")).fetchall()]

        units = ["UN", "KG", "LT", "M", "CX", "PC"]
        products_per_batch = self.config.batch_size
        total_batches = (self.config.num_products + products_per_batch - 1) // products_per_batch

        for batch_num in range(total_batches):
            start_idx = batch_num * products_per_batch + 1
            end_idx = min(start_idx + products_per_batch, self.config.num_products + 1)
            batch_size = end_idx - start_idx

            products_data = []
            now = datetime.now(UTC)
            for i in range(start_idx, end_idx):
                cost = random.randint(500, 50000)  # R$ 5,00 a R$ 500,00
                margin = random.randint(15, 80)  # 15% a 80%
                price = int(cost / (1 - margin / 100))

                products_data.append({
                    "company_id": self.company_id,
                    "sku": f"SKU{i:06d}",
                    "name": f"Produto {i}",
                    "description": f"Descrição do produto {i}",
                    "category_id": random.choice(category_ids),
                    "supplier_id": random.choice(supplier_ids) if supplier_ids else None,
                    "unit": random.choice(units),
                    "cost_cents": cost,
                    "margin_pct": margin,
                    "price_cents": price,
                    "min_stock_qty": random.randint(0, 100) * 1000,
                    "stock_qty": random.randint(0, 1000) * 1000,
                    "sold_by_weight": random.choice([0, 1]),
                    "active": 1,
                    "created_at": now,
                    "updated_at": now,
                })

            with self._get_session() as session:
                session.execute(text("""
                    INSERT INTO products (
                        company_id, sku, name, description, category_id, supplier_id,
                        unit, cost_cents, margin_pct, price_cents, min_stock_qty,
                        stock_qty, sold_by_weight, active, created_at, updated_at
                    ) VALUES (
                        :company_id, :sku, :name, :description, :category_id, :supplier_id,
                        :unit, :cost_cents, :margin_pct, :price_cents, :min_stock_qty,
                        :stock_qty, :sold_by_weight, :active, :created_at, :updated_at
                    )
                """), products_data)
                session.commit()

            if (batch_num + 1) % 10 == 0 or batch_num == total_batches - 1:
                print(f"    Lote {batch_num + 1}/{total_batches} ({end_idx - 1}/{self.config.num_products})")

        print(f"  ✅ {self.config.num_products} produtos criados")

    def _seed_sales(self) -> None:
        print(f"\n  💰 Criando {self.config.num_sales} vendas...")

        with self._get_session() as session:
            product_ids = [row[0] for row in session.execute(text("SELECT id FROM products WHERE company_id = 1 AND active = 1")).fetchall()]
            user_ids = [row[0] for row in session.execute(text("SELECT id FROM users WHERE company_id = 1")).fetchall()]
            user_names = {row[0]: row[1] for row in session.execute(text("SELECT id, employee_name FROM users WHERE company_id = 1")).fetchall()}
            register_ids = [row[0] for row in session.execute(text("SELECT id FROM cash_registers WHERE company_id = 1")).fetchall()]
            
            # Verifica qual é o próximo ID disponível
            max_sale_id = session.execute(text("SELECT COALESCE(MAX(id), 0) FROM sales")).scalar()
            sale_id_start = max_sale_id + 1

        payment_methods = ["Dinheiro", "PIX", "Cartão Débito", "Cartão Crédito", "Vale"]

        sales_per_batch = self.config.batch_size
        total_batches = (self.config.num_sales + sales_per_batch - 1) // sales_per_batch

        for batch_num in range(total_batches):
            start_idx = batch_num * sales_per_batch
            end_idx = min(start_idx + sales_per_batch, self.config.num_sales)
            batch_size = end_idx - start_idx

            sales_data = []
            items_data = []
            payments_data = []

            for i in range(batch_size):
                sale_id = sale_id_start + start_idx + i
                num_items = random.randint(1, 10)
                subtotal = 0

                # Venda
                sale_date = datetime.now(UTC) - timedelta(days=random.randint(0, 365))
                session_id = random.choice(register_ids) if register_ids else None
                user_id = random.choice(user_ids)
                status = "finalized"

                # Itens
                sale_items = random.sample(product_ids, min(num_items, len(product_ids)))
                for item_idx, product_id in enumerate(sale_items):
                    with self._get_session() as session:
                        product = session.get(ProductModel, product_id)
                        if not product:
                            continue
                        qty = random.randint(1, 20) * 1000
                        unit_price = product.price_cents
                        line_total = unit_price * qty
                        subtotal += line_total

                        items_data.append({
                            "sale_id": sale_id,
                            "company_id": self.company_id,
                            "product_id": product_id,
                            "description": product.name,
                            "unit_price_cents": unit_price,
                            "quantity_thousandths": qty,
                            "line_total_cents": line_total,
                            "unit": product.unit,
                            "cancelled": 0,
                            "cancel_reason": "",
                        })

                discount = random.randint(0, subtotal // 10) if subtotal > 1000 else 0
                total = subtotal - discount

                # Pagamentos
                remaining = total
                payments = []
                for _ in range(random.randint(1, 3)):
                    if remaining <= 0:
                        break
                    if len(payments) == 2:
                        amount = remaining
                    else:
                        amount = random.randint(1, remaining)
                    payments.append(amount)
                    remaining -= amount
                if remaining > 0:
                    payments[-1] += remaining

                for amount in payments:
                    method = random.choice(payment_methods)
                    change = 0
                    if method == "Dinheiro" and amount > total // len(payments):
                        change = amount - total // len(payments)
                    payments_data.append({
                        "sale_id": sale_id,
                        "company_id": self.company_id,
                        "method": method,
                        "amount_cents": amount,
                        "change_cents": change,
                    })

                sales_data.append({
                    "id": sale_id,
                    "company_id": self.company_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "username": user_names.get(user_id, f"user{user_id}"),
                    "status": status,
                    "subtotal_cents": subtotal,
                    "discount_cents": discount,
                    "total_cents": total,
                    "paid_cents": total,
                    "change_cents": sum(p.get("change_cents", 0) for p in payments_data[-len(payments):]),
                    "cancel_reason": "",
                    "cancelled_by_user_id": None,
                    "cancelled_by_username": "",
                    "authorized_by_user_id": None,
                    "authorized_by_username": "",
                    "created_at": sale_date,
                    "finalized_at": sale_date,
                    "cancelled_at": None,
                })

            with self._get_session() as session:
                if sales_data:
                    session.execute(text("""
                        INSERT INTO sales (
                            id, company_id, session_id, user_id, username, status,
                            subtotal_cents, discount_cents, total_cents, paid_cents,
                            change_cents, cancel_reason, cancelled_by_user_id,
                            cancelled_by_username, authorized_by_user_id,
                            authorized_by_username, created_at, finalized_at, cancelled_at
                        ) VALUES (
                            :id, :company_id, :session_id, :user_id, :username, :status,
                            :subtotal_cents, :discount_cents, :total_cents, :paid_cents,
                            :change_cents, :cancel_reason, :cancelled_by_user_id,
                            :cancelled_by_username, :authorized_by_user_id,
                            :authorized_by_username, :created_at, :finalized_at, :cancelled_at
                        )
                    """), sales_data)

                if items_data:
                    session.execute(text("""
                        INSERT INTO sale_items (
                            sale_id, company_id, product_id, description, unit_price_cents,
                            quantity_thousandths, line_total_cents, unit, cancelled, cancel_reason
                        ) VALUES (
                            :sale_id, :company_id, :product_id, :description, :unit_price_cents,
                            :quantity_thousandths, :line_total_cents, :unit, :cancelled, :cancel_reason
                        )
                    """), items_data)

                if payments_data:
                    session.execute(text("""
                        INSERT INTO sale_payments (
                            sale_id, company_id, method, amount_cents, change_cents
                        ) VALUES (
                            :sale_id, :company_id, :method, :amount_cents, :change_cents
                        )
                    """), payments_data)

                session.commit()

            if (batch_num + 1) % 10 == 0 or batch_num == total_batches - 1:
                print(f"    Lote {batch_num + 1}/{total_batches} ({end_idx - 1}/{self.config.num_sales})")

        print(f"  ✅ {self.config.num_sales} vendas criadas")

    def _seed_cash_sessions(self) -> None:
        print(f"\n  🏪 Criando sessões de caixa...")

        with self._get_session() as session:
            register_ids = [row[0] for row in session.execute(text("SELECT id FROM cash_registers WHERE company_id = 1")).fetchall()]
            user_ids = [row[0] for row in session.execute(text("SELECT id FROM users WHERE company_id = 1")).fetchall()]

            for register_id in register_ids:
                # Verifica se já tem sessão
                existing = session.execute(text("""
                    SELECT 1 FROM cash_sessions WHERE register_id = :rid AND status = 'open'
                """), {"rid": register_id}).fetchone()
                if existing:
                    continue

                opening = random.randint(10000, 50000)  # R$ 100 a R$ 500
                opened_by_user_id = random.choice(user_ids)
                with self._get_session() as s:
                    opened_by_username = s.execute(text("SELECT employee_name FROM users WHERE id = :uid"), {"uid": opened_by_user_id}).scalar() or f"user{opened_by_user_id}"

                session.execute(text("""
                    INSERT INTO cash_sessions (
                        register_id, company_id, opened_by_user_id, opened_by_username,
                        opened_at, opening_amount_cents, status,
                        closed_by_user_id, closed_by_username, closed_at,
                        closing_amount_cents, total_sales_cents, total_suprimentos_cents,
                        total_sangrias_cents, total_pix_cents, total_card_cents,
                        expected_cash_cents, difference_cents, closed, blind_close,
                        created_at, updated_at
                    ) VALUES (
                        :register_id, 1, :opened_by_user_id, :opened_by_username,
                        :opened_at, :opening_amount_cents, 'open',
                        0, '', NULL,
                        0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0,
                        :now, :now
                    )
                """), {
                    "register_id": register_id,
                    "opened_by_user_id": opened_by_user_id,
                    "opened_by_username": opened_by_username,
                    "opened_at": datetime.now(UTC) - timedelta(hours=random.randint(1, 8)),
                    "opening_amount_cents": opening,
                    "now": datetime.now(UTC),
                })

            session.commit()

        print(f"  ✅ Sessões de caixa criadas")

    def measure_performance(self) -> dict:
        """Mede performance de operações críticas."""
        print("\n" + "=" * 60)
        print("MEDINDO PERFORMANCE")
        print("=" * 60)

        results = {}

        # 1. App startup (bootstrap)
        results["bootstrap"] = self._measure_bootstrap()

        # 2. PDV busca por SKU
        results["pdv_sku_search"] = self._measure_pdv_sku_search()

        # 3. PDV busca por nome (prefixo)
        results["pdv_name_search"] = self._measure_pdv_name_search()

        # 4. PDV busca por nome (substring)
        results["pdv_name_substring"] = self._measure_pdv_name_substring()

        # 5. Relatório vendas por período
        results["report_sales_by_period"] = self._measure_report_sales_by_period()

        # 6. Relatório vendas por produto
        results["report_sales_by_product"] = self._measure_report_sales_by_product()

        # 7. Relatório estoque baixo
        results["report_low_stock"] = self._measure_report_low_stock()

        # 8. Relatório margem de lucro
        results["report_profit_margin"] = self._measure_report_profit_margin()

        # 9. Fechamento de caixa
        results["cash_closing"] = self._measure_cash_closing()

        # 10. Fluxo de caixa (treasury)
        results["treasury_cash_flow"] = self._measure_treasury_cash_flow()

        print("\n" + "=" * 60)
        print("RESUMO DE PERFORMANCE")
        print("=" * 60)
        for key, value in results.items():
            status = "✅" if value.get("ok", True) else "⚠️"
            print(f"  {status} {key}: {value['time_ms']:.2f}ms ({value.get('rows', 0)} rows)")

        return results

    def _measure_bootstrap(self) -> dict:
        start = time.perf_counter()
        ctx = bootstrap()
        elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 2000, "note": "Target: < 2s"}

    def _measure_pdv_sku_search(self) -> dict:
        with self._get_session() as session:
            sku = session.execute(text("SELECT sku FROM products WHERE company_id = 1 AND active = 1 ORDER BY RANDOM() LIMIT 1")).scalar()
            if not sku:
                return {"time_ms": 0, "ok": False, "note": "No products"}

            start = time.perf_counter()
            session.execute(text("""
                SELECT * FROM products WHERE company_id = 1 AND sku = :sku AND active = 1
            """), {"sku": sku}).fetchone()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 50, "note": "Target: < 50ms"}

    def _measure_pdv_name_search(self) -> dict:
        with self._get_session() as session:
            # Busca um nome existente e pega prefixo
            name = session.execute(text("SELECT name FROM products WHERE company_id = 1 AND active = 1 ORDER BY RANDOM() LIMIT 1")).scalar()
            if not name:
                return {"time_ms": 0, "ok": False, "note": "No products"}

            prefix = name[:5]  # primeiro 5 chars

            start = time.perf_counter()
            session.execute(text("""
                SELECT * FROM products
                WHERE company_id = 1 AND active = 1 AND name LIKE :prefix
                ORDER BY name LIMIT 20
            """), {"prefix": f"{prefix}%"}).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 100, "note": "Target: < 100ms"}

    def _measure_pdv_name_substring(self) -> dict:
        with self._get_session() as session:
            name = session.execute(text("SELECT name FROM products WHERE company_id = 1 AND active = 1 ORDER BY RANDOM() LIMIT 1")).scalar()
            if not name:
                return {"time_ms": 0, "ok": False, "note": "No products"}

            substr = name[3:8]  # meio do nome

            start = time.perf_counter()
            session.execute(text("""
                SELECT * FROM products
                WHERE company_id = 1 AND active = 1 AND name LIKE :substr
                ORDER BY name LIMIT 20
            """), {"substr": f"%{substr}%"}).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 500, "note": "Target: < 500ms (full scan esperado)"}

    def _measure_report_sales_by_period(self) -> dict:
        with self._get_session() as session:
            start = time.perf_counter()
            session.execute(text("""
                SELECT
                    date(s.created_at) as sale_date,
                    COALESCE(SUM(s.total_cents), 0) as total_sales,
                    COALESCE(SUM(si.quantity_thousandths), 0) as total_items,
                    COUNT(DISTINCT s.id) as total_transactions
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE s.company_id = 1
                AND s.created_at >= :start_date
                AND s.created_at <= :end_date
                GROUP BY date(s.created_at) ORDER BY sale_date
            """), {
                "start_date": datetime.now(UTC) - timedelta(days=30),
                "end_date": datetime.now(UTC),
            }).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 1000, "note": "Target: < 1s"}

    def _measure_report_sales_by_product(self) -> dict:
        with self._get_session() as session:
            start = time.perf_counter()
            session.execute(text("""
                SELECT
                    p.id as product_id,
                    p.name as product_name,
                    p.sku,
                    COALESCE(SUM(si.quantity_thousandths), 0) as quantity_sold,
                    COALESCE(SUM(si.line_total_cents), 0) as total_revenue,
                    CASE WHEN SUM(si.quantity_thousandths) > 0
                        THEN SUM(si.line_total_cents) / SUM(si.quantity_thousandths)
                        ELSE 0 END as avg_price
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE s.company_id = 1
                AND s.created_at >= :start_date
                AND s.created_at <= :end_date
                GROUP BY p.id, p.name, p.sku ORDER BY total_revenue DESC
            """), {
                "start_date": datetime.now(UTC) - timedelta(days=30),
                "end_date": datetime.now(UTC),
            }).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 2000, "note": "Target: < 2s"}

    def _measure_report_low_stock(self) -> dict:
        with self._get_session() as session:
            start = time.perf_counter()
            session.execute(text("""
                SELECT
                    p.id as product_id,
                    p.name as product_name,
                    p.sku,
                    p.stock_qty as current_stock,
                    p.min_stock_qty as min_stock,
                    c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.company_id = 1
                AND p.active = 1
                AND p.min_stock_qty > 0
                AND p.stock_qty <= p.min_stock_qty
                ORDER BY current_stock ASC, p.name
            """)).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 500, "note": "Target: < 500ms"}

    def _measure_report_profit_margin(self) -> dict:
        with self._get_session() as session:
            start = time.perf_counter()
            session.execute(text("""
                SELECT
                    p.id as product_id,
                    p.name as product_name,
                    p.sku,
                    p.cost_cents,
                    p.price_cents as sale_price_cents,
                    (p.price_cents - p.cost_cents) as margin_cents,
                    CASE WHEN p.price_cents > 0
                        THEN ((p.price_cents - p.cost_cents) * 100.0 / p.price_cents)
                        ELSE 0 END as margin_percent
                FROM products p
                WHERE p.company_id = 1
                AND p.active = 1
                ORDER BY margin_percent DESC
            """)).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 500, "note": "Target: < 500ms"}

    def _measure_cash_closing(self) -> dict:
        with self._get_session() as session:
            start = time.perf_counter()
            session.execute(text("""
                SELECT
                    cs.id as session_id,
                    cs.opened_at,
                    cs.closed_at,
                    u.employee_name as operator_name,
                    cs.opening_amount_cents,
                    cs.expected_cash_cents,
                    cs.closing_amount_cents as actual_amount,
                    COALESCE(cs.closing_amount_cents, 0) - COALESCE(cs.expected_cash_cents, 0) as difference,
                    COALESCE((
                        SELECT SUM(amount_cents) FROM cash_movements
                        WHERE session_id = cs.id AND movement_type = 'sangria'
                    ), 0) as sangrias,
                    COALESCE((
                        SELECT SUM(amount_cents) FROM cash_movements
                        WHERE session_id = cs.id AND movement_type = 'suprimento'
                    ), 0) as suprimentos
                FROM cash_sessions cs
                JOIN users u ON cs.opened_by_user_id = u.id
                WHERE cs.company_id = 1
                ORDER BY cs.opened_at DESC
            """)).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 500, "note": "Target: < 500ms"}

    def _measure_treasury_cash_flow(self) -> dict:
        with self._get_session() as session:
            start = time.perf_counter()
            session.execute(text("""
                SELECT
                    type,
                    SUM(amount_cents) as total
                FROM financial_entries
                WHERE company_id = 1
                AND date >= :start_date
                AND date <= :end_date
                GROUP BY type
            """), {
                "start_date": datetime.now(UTC) - timedelta(days=30),
                "end_date": datetime.now(UTC),
            }).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
        return {"time_ms": elapsed, "ok": elapsed < 500, "note": "Target: < 500ms"}

    def analyze_indexes(self) -> None:
        """Analisa índices existentes e sugere novos."""
        print("\n" + "=" * 60)
        print("ANÁLISE DE ÍNDICES")
        print("=" * 60)

        with self._get_session() as session:
            # Lista índices atuais
            indexes = session.execute(text("""
                SELECT name, tbl_name, sql FROM sqlite_master
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """)).fetchall()

            print("\nÍndices atuais:")
            by_table = {}
            for idx in indexes:
                table = idx[1]
                if table not in by_table:
                    by_table[table] = []
                by_table[table].append(idx[0])

            for table, idxs in sorted(by_table.items()):
                print(f"  {table}: {', '.join(idxs)}")

            # Análise de planos de query (EXPLAIN QUERY PLAN)
            print("\nAnálise de planos de query (EXPLAIN QUERY PLAN):")

            queries = [
                ("PDV SKU search", "SELECT * FROM products WHERE company_id = 1 AND sku = 'SKU000001' AND active = 1"),
                ("PDV Name prefix", "SELECT * FROM products WHERE company_id = 1 AND active = 1 AND name LIKE 'Prod%' ORDER BY name LIMIT 20"),
                ("Sales by period", """
                    SELECT date(s.created_at), SUM(s.total_cents), COUNT(DISTINCT s.id)
                    FROM sales s
                    WHERE s.company_id = 1 AND s.created_at >= date('now', '-30 days')
                    GROUP BY date(s.created_at)
                """),
                ("Sales by product", """
                    SELECT p.id, p.name, SUM(si.line_total_cents)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.company_id = 1 AND s.created_at >= date('now', '-30 days')
                    GROUP BY p.id
                """),
                ("Low stock", "SELECT * FROM products WHERE company_id = 1 AND active = 1 AND min_stock_qty > 0 AND stock_qty <= min_stock_qty"),
            ]

            for name, query in queries:
                print(f"\n  {name}:")
                plan = session.execute(text(f"EXPLAIN QUERY PLAN {query}")).fetchall()
                for row in plan:
                    print(f"    {row[3]}")


def main():
    parser = argparse.ArgumentParser(description="Load test para NexoERP (Task 5.1)")
    parser.add_argument("--seed", action="store_true", help="Executa seeding de 50k produtos e 100k vendas")
    parser.add_argument("--measure", action="store_true", help="Mede performance das operações críticas")
    parser.add_argument("--analyze", action="store_true", help="Analisa índices e planos de query")
    parser.add_argument("--products", type=int, default=50_000, help="Número de produtos")
    parser.add_argument("--sales", type=int, default=100_000, help="Número de vendas")

    args = parser.parse_args()

    if not (args.seed or args.measure or args.analyze):
        parser.print_help()
        return

    config = LoadTestConfig(
        num_products=args.products,
        num_sales=args.sales,
    )

    tester = LoadTester(config)

    if args.seed:
        tester.seed_all()

    if args.measure:
        tester.measure_performance()

    if args.analyze:
        tester.analyze_indexes()


if __name__ == "__main__":
    main()