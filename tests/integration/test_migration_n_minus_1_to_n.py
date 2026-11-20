"""Migration test N-1 to N — verifica que dados sobrevivem a upgrade de esquema.

Cria um banco em uma versao anterior (N-1), insere dados de teste,
roda upgrade para head e verifica integridade dos dados.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

N_MINUS_1_REVISION = "6d9acc35f851"
HEAD_REVISION = "d3d407b12fb7"


def _alembic_cfg(db_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _upgrade_to(revision: str, db_url: str) -> None:
    cfg = _alembic_cfg(db_url)
    command.upgrade(cfg, revision)


def _current_revision(db_url: str) -> str | None:
    _alembic_cfg(db_url)
    from alembic.runtime.migration import MigrationContext

    engine = create_engine(db_url, future=True)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def test_migration_n_minus_1_to_n_preserves_data(tmp_path: Path) -> None:
    """Upgrade de N-1 para head preserva dados existentes."""
    db_path = tmp_path / "erp_migration_test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    # 1. Criar banco na versao N-1
    _upgrade_to(N_MINUS_1_REVISION, db_url)
    assert _current_revision(db_url) == N_MINUS_1_REVISION

    # 2. Inserir dados de teste nas tabelas que existem em N-1
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO companies (
                id, company_id, name, trade_name, tax_id, active, created_at, updated_at
            )
            VALUES (
                1, 1, 'Empresa Teste', 'Empresa Teste', '00.000.000/0001-00',
                1, datetime('now'), datetime('now')
            )
        """)
        )
        conn.execute(
            text("""
            INSERT INTO categories (
                company_id, name, description, parent_id, is_active,
                created_at, updated_at
            )
            VALUES (1, 'Categoria Teste', 'Descricao', NULL, 1, datetime('now'), datetime('now'))
        """)
        )
        conn.execute(
            text("""
            INSERT INTO suppliers (
                company_id, name, trade_name, tax_id, contact_name,
                phone, email, is_active, created_at, updated_at
            )
            VALUES (
                1, 'Fornecedor Teste', 'Teste', '00.000.000/0001-00', 'Contato',
                '(11) 99999-9999', 'teste@teste.com', 1, datetime('now'), datetime('now')
            )
        """)
        )
        result = conn.execute(
            text("""
            INSERT INTO products (
                company_id, sku, name, description, category_id, supplier_id, unit,
                cost_cents, margin_pct, price_cents, min_stock_qty, stock_qty,
                sold_by_weight, active, created_at, updated_at
            )
            VALUES (
                1, 'SKU000001', 'Produto Teste', 'Descricao', 1, 1, 'UN',
                1000, 3000, 1300, 10000, 50000, 0, 1,
                datetime('now'), datetime('now')
            )
            RETURNING id
        """)
        )
        product_id = result.scalar_one()
        assert product_id is not None

        result = conn.execute(
            text("""
            INSERT INTO sales (
                company_id, session_id, user_id, username, status,
                subtotal_cents, discount_cents, total_cents, paid_cents, change_cents,
                cancel_reason, cancelled_by_user_id, cancelled_by_username,
                authorized_by_user_id, authorized_by_username, created_at,
                finalized_at, cancelled_at
            )
            VALUES (
                1, NULL, NULL, 'operador', 'finalized',
                1300, 0, 1300, 1300, 0,
                '', NULL, '', NULL, '', datetime('now'), datetime('now'), NULL
            )
            RETURNING id
        """)
        )
        sale_id = result.scalar_one()
        assert sale_id is not None

        conn.execute(
            text("""
            INSERT INTO sale_items (
                sale_id, company_id, product_id, description, unit_price_cents,
                quantity_thousandths, line_total_cents, unit, cancelled, cancel_reason
            )
            VALUES (1, 1, :pid, 'Produto Teste', 1300, 1000, 1300, 'UN', 0, '')
        """),
            {"pid": product_id},
        )

        conn.execute(
            text("""
            INSERT INTO sale_payments (sale_id, company_id, method, amount_cents, change_cents)
            VALUES (1, 1, 'dinheiro', 1300, 0)
        """)
        )

    # 3. Upgrade para head
    _upgrade_to(HEAD_REVISION, db_url)
    assert _current_revision(db_url) == HEAD_REVISION

    # 4. Verificar que os dados ainda existem
    with engine.connect() as conn:
        company = conn.execute(text("SELECT name FROM companies WHERE id = 1")).scalar_one()
        assert company == "Empresa Teste"

        product = conn.execute(
            text("SELECT name, sku FROM products WHERE id = :pid"), {"pid": product_id}
        ).fetchone()
        assert product is not None
        assert product[0] == "Produto Teste"
        assert product[1] == "SKU000001"

        sale = conn.execute(
            text("SELECT total_cents FROM sales WHERE id = :sid"), {"sid": sale_id}
        ).fetchone()
        assert sale is not None
        assert sale[0] == 1300

        item_count = conn.execute(
            text("SELECT COUNT(*) FROM sale_items WHERE sale_id = :sid"), {"sid": sale_id}
        ).scalar_one()
        assert item_count == 1

        payment_count = conn.execute(
            text("SELECT COUNT(*) FROM sale_payments WHERE sale_id = :sid"), {"sid": sale_id}
        ).scalar_one()
        assert payment_count == 1

    # 5. Verificar que tabelas essenciais continuam existindo
    with engine.connect() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }
        assert "companies" in tables
        assert "products" in tables
        assert "sales" in tables
        assert "sale_items" in tables
        assert "sale_payments" in tables
