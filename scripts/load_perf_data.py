#!/usr/bin/env python3
"""Performance data loading script.

Generates 50k products and 100k sales for performance testing.
Measures app startup, PDV search, and cash closing performance.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session

from erp.config.paths import get_data_dir
from erp.shared.infrastructure.database.engine import build_engine


def get_company_id(session: Session) -> int:
    """Get or create a test company."""
    result = session.execute(text("SELECT id FROM companies LIMIT 1")).fetchone()
    if result:
        return result[0]
    # Create a company
    session.execute(
        text(
            "INSERT INTO companies (company_id, name, trade_name, tax_id, address, active, created_at, updated_at) "
            "VALUES (1, 'Empresa Teste', 'Teste', '00.000.000/0001-00', 'Rua Teste, 123', 1, datetime('now'), datetime('now'))"
        )
    )
    session.commit()
    return session.execute(text("SELECT last_insert_rowid()")).scalar()


def get_category_id(session: Session, company_id: int) -> int:
    """Get or create a test category."""
    result = session.execute(
        text("SELECT id FROM categories WHERE company_id = :cid LIMIT 1"),
        {"cid": company_id},
    ).fetchone()
    if result:
        return result[0]
    session.execute(
        text(
            "INSERT INTO categories (company_id, name, description, parent_id, is_active, created_at, updated_at) "
            "VALUES (:cid, 'Categoria Teste', 'Descrição', NULL, 1, datetime('now'), datetime('now'))"
        ),
        {"cid": company_id},
    )
    session.commit()
    return session.execute(text("SELECT last_insert_rowid()")).scalar()


def get_supplier_id(session: Session, company_id: int) -> int:
    """Get or create a test supplier."""
    result = session.execute(
        text("SELECT id FROM suppliers WHERE company_id = :cid LIMIT 1"),
        {"cid": company_id},
    ).fetchone()
    if result:
        return result[0]
    session.execute(
        text(
            "INSERT INTO suppliers (company_id, name, trade_name, tax_id, contact_name, phone, email, address, is_active, created_at, updated_at) "
            "VALUES (:cid, 'Fornecedor Teste', 'Teste', '00.000.000/0001-00', 'Contato', '(11) 99999-9999', 'teste@teste.com', 'Rua Fornecedor, 456', 1, datetime('now'), datetime('now'))"
        ),
        {"cid": company_id},
    )
    session.commit()
    return session.execute(text("SELECT last_insert_rowid()")).scalar()


def get_user_id(session: Session, company_id: int) -> int:
    """Get or create a test user."""
    result = session.execute(
        text("SELECT id FROM users WHERE company_id = :cid LIMIT 1"),
        {"cid": company_id},
    ).fetchone()
    if result:
        return result[0]
    # Create user with bcrypt hash for 'password'
    from erp.modules.identity.infrastructure.hasher import BcryptHasher
    hasher = BcryptHasher()
    password_hash = hasher.hash("password")
    session.execute(
        text(
            "INSERT INTO users (company_id, username, password_hash, must_change_password, failed_login_attempts, is_active, created_at, updated_at) "
            "VALUES (:cid, 'operador', :ph, 0, 0, 1, datetime('now'), datetime('now'))"
        ),
        {"cid": company_id, "ph": password_hash},
    )
    session.commit()
    return session.execute(text("SELECT last_insert_rowid()")).scalar()


def get_cash_register_id(session: Session, company_id: int) -> int:
    """Get or create a test cash register."""
    result = session.execute(
        text("SELECT id FROM cash_registers WHERE company_id = :cid LIMIT 1"),
        {"cid": company_id},
    ).fetchone()
    if result:
        return result[0]
    session.execute(
        text(
            "INSERT INTO cash_registers (company_id, name, terminal_code, active, created_at, updated_at) "
            "VALUES (:cid, 'Caixa 1', 'CAIXA01', 1, datetime('now'), datetime('now'))"
        ),
        {"cid": company_id},
    )
    session.commit()
    return session.execute(text("SELECT last_insert_rowid()")).scalar()


def load_products(session: Session, company_id: int, category_id: int, supplier_id: int, count: int) -> list[int]:
    """Load products in batches."""
    print(f"Loading {count} products...")
    start = time.perf_counter()

    product_ids = []
    batch_size = 1000

    for i in range(0, count, batch_size):
        batch = []
        for j in range(batch_size):
            idx = i + j + 1
            sku = f"SKU{idx:06d}"
            name = f"Produto {idx}"
            cost_cents = random.randint(100, 100000)
            margin_pct = random.randint(10, 100)
            price_cents = int(cost_cents * (1 + margin_pct / 100))
            stock_qty = random.randint(0, 1000)
            min_stock = random.randint(0, 20)

            batch.append(
                {
                    "company_id": company_id,
                    "sku": sku,
                    "name": name,
                    "description": f"Descrição do produto {idx}",
                    "category_id": category_id,
                    "supplier_id": supplier_id,
                    "unit": "UN",
                    "cost_cents": cost_cents,
                    "margin_pct": margin_pct,
                    "price_cents": price_cents,
                    "min_stock_qty": min_stock,
                    "stock_qty": stock_qty,
                    "sold_by_weight": 0,
                    "active": 1,
                    "created_at": datetime.now(UTC).replace(tzinfo=None),
                    "updated_at": datetime.now(UTC).replace(tzinfo=None),
                }
            )

        session.execute(
            text(
                "INSERT INTO products (company_id, sku, name, description, category_id, supplier_id, unit, "
                "cost_cents, margin_pct, price_cents, min_stock_qty, stock_qty, sold_by_weight, active, created_at, updated_at) "
                "VALUES (:company_id, :sku, :name, :description, :category_id, :supplier_id, :unit, "
                ":cost_cents, :margin_pct, :price_cents, :min_stock_qty, :stock_qty, :sold_by_weight, :active, :created_at, :updated_at)"
            ),
            batch,
        )
        session.commit()

        # Get inserted IDs
        for _item in batch:
            product_ids.append(session.execute(text("SELECT last_insert_rowid()")).scalar())

        if (i + batch_size) % 10000 == 0:
            elapsed = time.perf_counter() - start
            print(f"  {min(i + batch_size, count)}/{count} products ({elapsed:.1f}s)")

    elapsed = time.perf_counter() - start
    print(f"Products loaded in {elapsed:.1f}s ({count/elapsed:.0f} products/s)")
    return product_ids


def load_sales(
    session: Session,
    company_id: int,
    product_ids: list[int],
    user_id: int,
    register_id: int,
    count: int,
) -> None:
    """Load sales in batches."""
    print(f"Loading {count} sales...")
    start = time.perf_counter()

    batch_size = 100
    base_date = datetime.now(UTC) - timedelta(days=30)

    for i in range(0, count, batch_size):
        for j in range(batch_size):
            i + j + 1
            sale_date = base_date + timedelta(
                minutes=random.randint(0, 43200)  # 30 days in minutes
            )

            # Create sale
            num_items = random.randint(1, 5)
            selected_products = random.sample(product_ids, min(num_items, len(product_ids)))

            subtotal = 0
            items_data = []
            for product_id in selected_products:
                product = session.execute(
                    text("SELECT price_cents, name, unit FROM products WHERE id = :pid"),
                    {"pid": product_id},
                ).fetchone()
                if not product:
                    continue
                price_cents, prod_name, unit = product
                qty = random.randint(1, 10)
                line_total = price_cents * qty
                subtotal += line_total
                items_data.append(
                    {
                        "product_id": product_id,
                        "description": prod_name,
                        "unit_price_cents": price_cents,
                        "quantity_thousandths": qty * 1000,
                        "line_total_cents": line_total,
                        "unit": unit,
                        "cancelled": 0,
                        "cancel_reason": "",
                    }
                )

            discount = random.randint(0, subtotal // 10)
            total = subtotal - discount
            paid = total
            change = 0

            # Insert sale
            session.execute(
                text(
                    "INSERT INTO sales (company_id, session_id, user_id, username, status, "
                    "subtotal_cents, discount_cents, total_cents, paid_cents, change_cents, "
                    "cancel_reason, cancelled_by_user_id, cancelled_by_username, "
                    "authorized_by_user_id, authorized_by_username, created_at, finalized_at) "
                    "VALUES (:cid, :sid, :uid, :uname, 'finalized', "
                    ":subtotal, :discount, :total, :paid, :change, "
                    "'', NULL, '', NULL, '', :created, :finalized)"
                ),
                {
                    "cid": company_id,
                    "sid": 1,  # We'll create a session
                    "uid": user_id,
                    "uname": "operador",
                    "subtotal": subtotal,
                    "discount": discount,
                    "total": total,
                    "paid": paid,
                    "change": change,
                    "created": sale_date.replace(tzinfo=None),
                    "finalized": sale_date.replace(tzinfo=None),
                },
            )
            sale_id = session.execute(text("SELECT last_insert_rowid()")).scalar()

            # Insert sale items
            for item in items_data:
                session.execute(
                    text(
                        "INSERT INTO sale_items (sale_id, company_id, product_id, description, "
                        "unit_price_cents, quantity_thousandths, line_total_cents, unit, cancelled, cancel_reason) "
                        "VALUES (:sid, :cid, :product_id, :description, :unit_price_cents, :quantity_thousandths, :line_total_cents, :unit, :cancelled, :cancel_reason)"
                    ),
                    {
                        "sid": sale_id,
                        "cid": company_id,
                        **item,
                    },
                )

            # Insert sale payment
            session.execute(
                text(
                    "INSERT INTO sale_payments (sale_id, company_id, method, amount_cents, change_cents) "
                    "VALUES (:sid, :cid, 'dinheiro', :amount, 0)"
                ),
                {"sid": sale_id, "cid": company_id, "amount": total},
            )

        session.commit()

        if (i + batch_size) % 10000 == 0:
            elapsed = time.perf_counter() - start
            print(f"  {min(i + batch_size, count)}/{count} sales ({elapsed:.1f}s)")

    elapsed = time.perf_counter() - start
    print(f"Sales loaded in {elapsed:.1f}s ({count/elapsed:.0f} sales/s)")


def load_cash_session(
    session: Session,
    company_id: int,
    register_id: int,
    user_id: int,
) -> int:
    """Create a cash session for the sales."""
    session.execute(
        text(
            "INSERT INTO cash_sessions (register_id, company_id, opened_by_user_id, opened_by_username, "
            "opened_at, opening_amount_cents, closed_by_user_id, closed_by_username, "
            "closed_at, closing_amount_cents, total_sales_cents, total_suprimentos_cents, "
            "total_sangrias_cents, total_pix_cents, total_card_cents, expected_cash_cents, "
            "difference_cents, status, closed, blind_close, created_at, updated_at) "
            "VALUES (:rid, :cid, :uid, 'operador', datetime('now'), 10000, "
            ":uid, 'operador', datetime('now'), 10000, 0, 0, 0, 0, 0, 10000, 0, 'closed', 1, 0, datetime('now'), datetime('now'))"
        ),
        {"rid": register_id, "cid": company_id, "uid": user_id},
    )
    session.commit()
    return session.execute(text("SELECT last_insert_rowid()")).scalar()


def measure_performance(db_path: str) -> dict:
    """Measure performance of key operations."""
    engine = build_engine(Path(db_path))
    results = {}

    with Session(engine) as session:
        # 1. App startup - run migrations and basic queries
        start = time.perf_counter()
        session.execute(text("SELECT 1"))
        results["startup_query"] = time.perf_counter() - start

        # 2. PDV search by name (prefix)
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT id, name, price_cents, stock_qty FROM products "
                "WHERE company_id = 1 AND name LIKE 'Produto 1%' AND active = 1 "
                "LIMIT 20"
            )
        ).fetchall()
        results["pdv_name_search"] = time.perf_counter() - start

        # 3. PDV search by SKU (exact)
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT id, name, price_cents, stock_qty FROM products "
                "WHERE company_id = 1 AND sku = 'SKU000001' AND active = 1"
            )
        ).fetchall()
        results["pdv_sku_search"] = time.perf_counter() - start

        # 4. PDV search by name (contains)
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT id, name, price_cents, stock_qty FROM products "
                "WHERE company_id = 1 AND name LIKE '%50000%' AND active = 1 "
                "LIMIT 20"
            )
        ).fetchall()
        results["pdv_contains_search"] = time.perf_counter() - start

        # 5. Cash closing query
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT cs.id, cs.opened_at, cs.closed_at, cs.opening_amount_cents, "
                "cs.expected_cash_cents, cs.closing_amount_cents, cs.difference_cents, "
                "cs.total_sales_cents, cs.total_sangrias_cents, cs.total_suprimentos_cents "
                "FROM cash_sessions cs "
                "WHERE cs.company_id = 1 AND cs.status = 'closed' "
                "ORDER BY cs.opened_at DESC LIMIT 10"
            )
        ).fetchall()
        results["cash_closing"] = time.perf_counter() - start

        # 6. Sales by period (report)
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT date(s.created_at) as sale_date, "
                "COALESCE(SUM(s.total_cents), 0) as total_sales, "
                "COALESCE(SUM(si.quantity_thousandths), 0) / 1000.0 as total_items, "
                "COUNT(DISTINCT s.id) as total_transactions "
                "FROM sales s "
                "LEFT JOIN sale_items si ON s.id = si.sale_id "
                "WHERE s.company_id = 1 AND s.status = 'finalized' "
                "AND s.created_at >= datetime('now', '-30 days') "
                "GROUP BY date(s.created_at) ORDER BY sale_date"
            )
        ).fetchall()
        results["sales_by_period"] = time.perf_counter() - start

        # 7. Low stock report
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT p.id, p.name, p.sku, p.stock_qty as current_stock, "
                "p.min_stock_qty, c.name as category_name "
                "FROM products p "
                "LEFT JOIN categories c ON p.category_id = c.id "
                "WHERE p.company_id = 1 AND p.active = 1 AND p.min_stock_qty > 0 "
                "AND p.stock_qty <= p.min_stock_qty "
                "ORDER BY current_stock ASC"
            )
        ).fetchall()
        results["low_stock"] = time.perf_counter() - start

        # 8. Profit margin report
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT p.id, p.name, p.sku, p.cost_cents, p.price_cents, "
                "(p.price_cents - p.cost_cents) as margin_amount, "
                "CASE WHEN p.price_cents > 0 THEN ((p.price_cents - p.cost_cents) * 100.0 / p.price_cents) ELSE 0 END as margin_percent "
                "FROM products p "
                "WHERE p.company_id = 1 AND p.active = 1 "
                "ORDER BY margin_percent DESC"
            )
        ).fetchall()
        results["profit_margin"] = time.perf_counter() - start

        # 9. Simple DRE (using financial_entries for expenses)
        start = time.perf_counter()
        session.execute(
            text(
                "SELECT 'receita' as category, 'Vendas' as description, COALESCE(SUM(s.total_cents), 0) as amount "
                "FROM sales s WHERE s.company_id = 1 AND s.status = 'finalized' "
                "UNION ALL "
                "SELECT 'despesa' as category, 'Despesas' as description, COALESCE(SUM(fe.amount_cents), 0) as amount "
                "FROM financial_entries fe "
                "WHERE fe.company_id = 1 AND fe.type = 'expense' "
                "GROUP BY category, description"
            )
        ).fetchall()
        results["simple_dre"] = time.perf_counter() - start

    return results


def print_results(results: dict) -> None:
    """Print performance results in a table."""
    print("\n" + "=" * 60)
    print("PERFORMANCE RESULTS")
    print("=" * 60)
    print(f"{'Operation':<30} {'Time (ms)':>12} {'Status':<10}")
    print("-" * 60)

    thresholds = {
        "startup_query": 10,
        "pdv_name_search": 50,
        "pdv_sku_search": 10,
        "pdv_contains_search": 100,
        "cash_closing": 100,
        "sales_by_period": 200,
        "low_stock": 200,
        "profit_margin": 200,
        "simple_dre": 300,
    }

    for op, time_sec in results.items():
        time_ms = time_sec * 1000
        threshold = thresholds.get(op, 500)
        status = "✓ OK" if time_ms < threshold else "⚠ SLOW"
        print(f"{op:<30} {time_ms:>10.1f} {status:<10}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Load performance test data")
    parser.add_argument("--products", type=int, default=50000, help="Number of products")
    parser.add_argument("--sales", type=int, default=100000, help="Number of sales")
    parser.add_argument("--db-path", type=str, help="Database path")
    parser.add_argument("--skip-load", action="store_true", help="Skip data loading, only measure")
    parser.add_argument("--measure-only", action="store_true", help="Only run measurements")
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else get_data_dir() / "erp.db"

    print(f"Database: {db_path}")
    engine = build_engine(db_path)

    with Session(engine) as session:
        # Ensure tables exist
        session.execute(text("SELECT 1 FROM products LIMIT 1"))
        session.execute(text("SELECT 1 FROM sales LIMIT 1"))

        if not args.skip_load and not args.measure_only:
            company_id = get_company_id(session)
            category_id = get_category_id(session, company_id)
            supplier_id = get_supplier_id(session, company_id)
            user_id = get_user_id(session, company_id)
            register_id = get_cash_register_id(session, company_id)

            # Load products
            product_ids = load_products(session, company_id, category_id, supplier_id, args.products)

            # Create cash session
            session_id = load_cash_session(session, company_id, register_id, user_id)
            print(f"Created cash session: {session_id}")

            # Load sales
            load_sales(session, company_id, product_ids, user_id, register_id, args.sales)

            print("Data loading complete!")

    # Measure performance
    print("\nMeasuring performance...")
    results = measure_performance(str(db_path))
    print_results(results)


if __name__ == "__main__":
    main()