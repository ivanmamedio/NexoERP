"""Testes de compatibilidade entre sistemas operacionais.

Verifica que o código funciona corretamente independentemente do SO
(Windows 10+, Linux Debian/Ubuntu).
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

import pytest


@pytest.mark.compatibility
def test_python_version_compatible():
    """Verifica que a versão do Python é compatível (3.12+)."""
    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 12), f"Python {major}.{minor} não é suportado. Requer 3.12+"


@pytest.mark.compatibility
def test_platform_supported():
    """Verifica que o sistema operacional é suportado."""
    system = platform.system()
    assert system in ("Windows", "Linux"), f"Sistema não suportado: {system}"


@pytest.mark.compatibility
def test_data_dir_platform_compatible():
    """Verifica que o diretório de dados funciona no SO atual."""
    from erp.config.paths import get_data_dir

    data_dir = get_data_dir()
    assert data_dir is not None
    assert isinstance(data_dir, Path)


@pytest.mark.compatibility
def test_import_all_modules():
    """Verifica que todos os módulos podem ser importados no SO atual."""
    modules = [
        "erp",
        "erp.bootstrap",
        "erp.config.paths",
        "erp.config.settings",
        "erp.shared.domain",
        "erp.shared.application.events",
        "erp.shared.application.session",
        "erp.shared.infrastructure.database",
        "erp.modules.identity",
        "erp.modules.companies",
        "erp.modules.catalog",
        "erp.modules.cash",
        "erp.modules.sales",
        "erp.modules.treasury",
        "erp.modules.audit",
        "erp.modules.backup",
        "erp.modules.reports",
        "erp.modules.receipts",
        "erp.modules.settings",
        "erp.modules.pricing",
        "erp.modules.purchases",
        "erp.modules.import_csv",
        "erp.modules.customers",
        "erp.modules.credit_notebook",
        "erp.modules.fiscal",
    ]
    for mod_name in modules:
        __import__(mod_name)


@pytest.mark.compatibility
def test_sqlite_pragma_compatible():
    """Verifica que as PRAGMAs do SQLite funcionam no SO atual."""
    from sqlalchemy import create_engine, text

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA journal_mode")).scalar()
        assert result in ("wal", "memory")


@pytest.mark.compatibility
def test_path_separator_platform():
    """Verifica que os separadores de caminho são corretos para o SO."""
    from pathlib import Path

    path = Path("a") / "b" / "c"
    if os.name == "nt":  # Windows
        assert "\\" in str(path)
    else:  # Linux
        assert "/" in str(path)


@pytest.mark.compatibility
def test_database_backup_compatible():
    """Verifica que o backup do SQLite funciona no SO atual."""
    import sqlite3
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        conn = sqlite3.connect(tmp_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test (id) VALUES (1)")
        conn.commit()

        # Testa backup
        backup_conn = sqlite3.connect(":memory:")
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@pytest.mark.compatibility
def test_utf8_encoding_compatible():
    """Verifica que strings UTF-8 funcionam corretamente."""
    text = "São Paulo - R$ 100,00 - Produto teste"
    encoded = text.encode("utf-8")
    decoded = encoded.decode("utf-8")
    assert decoded == text


@pytest.mark.compatibility
def test_import_linter_contracts():
    """Verifica que os contratos de import-linter estão definidos."""
    from pathlib import Path

    import_linter_file = Path(__file__).parent.parent.parent / ".importlinter"
    assert import_linter_file.exists()
    content = import_linter_file.read_text()
    assert "no-infrastructure-imports" in content
    assert "shared-domain-purity" in content


@pytest.mark.compatibility
def test_alembic_migrations_discoverable():
    """Verifica que as migrações do Alembic são detectáveis."""
    from pathlib import Path

    alembic_dir = (
        Path(__file__).parent.parent.parent
        / "src"
        / "erp"
        / "shared"
        / "infrastructure"
        / "database"
        / "alembic"
    )
    assert alembic_dir.exists()
    versions_dir = alembic_dir / "versions"
    assert versions_dir.exists()
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) > 0


@pytest.mark.compatibility
def test_receipts_float_not_used_for_money():
    """Verifica que o módulo receipts não usa float para quantidade."""
    import ast
    from pathlib import Path

    receipts_domain = (
        Path(__file__).parent.parent.parent
        / "src"
        / "erp"
        / "modules"
        / "receipts"
        / "domain"
        / "__init__.py"
    )
    assert receipts_domain.exists()

    with receipts_domain.open() as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if arg.arg == "quantity" and arg.annotation:
                    # Deve ser int (milésimos), não float
                    annotation_str = ast.unparse(arg.annotation)
                    assert "float" not in annotation_str, (
                        f"quantity deve ser int (milésimos), não float."
                        f" Encontrado: {annotation_str}"
                    )


@pytest.mark.compatibility
def test_no_platform_specific_paths():
    """Verifica que não há caminhos específicos de plataforma no código."""
    from pathlib import Path

    src_dir = Path(__file__).parent.parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Verifica se não há caminhos absolutos do Windows ou Linux específicos
        if "C:\\" in content or "/home/" in content:
            pytest.fail(f"Caminho específico de plataforma encontrado em {py_file}")


@pytest.mark.compatibility
def test_no_windows_specific_api():
    """Verifica que não há APIs específicas do Windows no código principal."""
    from pathlib import Path

    src_dir = Path(__file__).parent.parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if "win32" in py_file.name.lower() or "msvc" in py_file.name.lower():
            continue  # Arquivos específicos do Windows são esperados
        content = py_file.read_text(encoding="utf-8")
        if "win32api" in content or "win32con" in content or "msvcrt" in content:
            pytest.fail(f"API específica do Windows encontrada em {py_file}")


@pytest.mark.compatibility
def test_no_linux_specific_api():
    """Verifica que não há APIs específicas do Linux no código principal."""
    from pathlib import Path

    src_dir = Path(__file__).parent.parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Evita falsos positivos em comentários
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Remove comentários
            if "#" in line:
                line = line[: line.index("#")]
            # Verifica imports específicos do Linux (apenas imports reais de módulo)
            stripped = line.strip()
            if stripped.startswith(
                ("import fcntl", "import resource", "from fcntl", "from resource")
            ):
                pytest.fail(f"API específica do Linux encontrada em {py_file}:{i}")


@pytest.mark.compatibility
def test_no_hardcoded_paths():
    """Verifica que não há caminhos fixos no código."""
    from pathlib import Path

    src_dir = Path(__file__).parent.parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Verifica strings que parecem caminhos fixos
        for line_num, line in enumerate(content.split("\n"), 1):
            # Remove comentários
            if "#" in line:
                line = line[: line.index("#")]
            stripped_line = line.strip()
            if stripped_line.startswith(('"/', "'/")):
                # Pode ser um caminho relativo, permite
                continue
            if '"C:' in line and line.strip().startswith('"C:'):
                pytest.fail(f"Caminho fixo do Windows encontrado em {py_file}:{line_num}")


@pytest.mark.compatibility
def test_import_all_presentation_modules():
    """Verifica que todos os módulos de presentation podem ser importados."""
    presentation_modules = [
        "erp.modules.identity.presentation.login_view",
        "erp.modules.identity.presentation.login_presenter",
        "erp.modules.identity.presentation.users_view",
        "erp.modules.identity.presentation.users_presenter",
        "erp.modules.catalog.presentation.catalog_dialog",
        "erp.modules.catalog.presentation.product_presenter",
        "erp.modules.catalog.presentation.price_dialog",
        "erp.modules.cash.presentation.open_cash_session_presenter",
        "erp.modules.cash.presentation.close_cash_session_presenter",
        "erp.modules.sales.presentation.pos_presenter",
        "erp.modules.sales.presentation.pos_view",
        "erp.modules.treasury.presentation.treasury_presenter",
        "erp.modules.treasury.presentation.treasury_dashboard",
        "erp.modules.receipts.presentation.preview",
        "erp.modules.settings.presentation.settings_view",
        "erp.modules.backup.presentation.restore",
        "erp.modules.audit.presentation.audit_view",
    ]
    for mod_name in presentation_modules:
        __import__(mod_name)


@pytest.mark.compatibility
def test_import_all_application_modules():
    """Verifica que todos os módulos de application podem ser importados."""
    application_modules = [
        "erp.modules.identity.application.services",
        "erp.modules.identity.application.authenticate",
        "erp.modules.identity.application.create_user",
        "erp.modules.catalog.application.services",
        "erp.modules.cash.application.services",
        "erp.modules.sales.application.services",
        "erp.modules.treasury.application.services",
        "erp.modules.reports.application.service",
        "erp.modules.receipts.application.generate_receipt",
        "erp.modules.backup.application.service",
        "erp.modules.audit.application.services",
        "erp.modules.settings.application.services",
        "erp.modules.pricing.application.services",
        "erp.modules.purchases.application.services",
        "erp.modules.import_csv.application.services",
        "erp.modules.customers.application.services",
        "erp.modules.credit_notebook.application.services",
        "erp.modules.fiscal.application.ports",
    ]
    for mod_name in application_modules:
        __import__(mod_name)


@pytest.mark.compatibility
def test_import_all_domain_modules():
    """Verifica que todos os módulos de domain podem ser importados."""
    domain_modules = [
        "erp.modules.identity.domain.user",
        "erp.modules.identity.domain.role",
        "erp.modules.identity.domain.permission",
        "erp.modules.catalog.domain.product",
        "erp.modules.catalog.domain.category",
        "erp.modules.catalog.domain.supplier",
        "erp.modules.cash.domain.cash_session",
        "erp.modules.cash.domain.cash_register",
        "erp.modules.sales.domain.sale",
        "erp.modules.treasury.domain.payable",
        "erp.modules.treasury.domain.receivable",
        "erp.modules.treasury.domain.financial_entry",
        "erp.modules.receipts.domain.__init__",
        "erp.modules.settings.domain.setting",
        "erp.modules.backup.domain.__init__",
        "erp.modules.audit.domain.audit_log",
        "erp.modules.pricing.domain.__init__",
        "erp.modules.purchases.domain.__init__",
        "erp.modules.import_csv.domain.__init__",
        "erp.modules.customers.domain.__init__",
        "erp.modules.credit_notebook.domain.__init__",
        "erp.modules.fiscal.domain.__init__",
    ]
    for mod_name in domain_modules:
        __import__(mod_name)


@pytest.mark.compatibility
def test_import_all_infrastructure_modules():
    """Verifica que todos os módulos de infrastructure podem ser importados."""
    infrastructure_modules = [
        "erp.modules.identity.infrastructure.repository",
        "erp.modules.identity.infrastructure.hasher",
        "erp.modules.catalog.infrastructure.repository",
        "erp.modules.cash.infrastructure.repository",
        "erp.modules.sales.infrastructure.repository",
        "erp.modules.treasury.infrastructure.repository",
        "erp.modules.receipts.infrastructure.__init__",
        "erp.modules.backup.infrastructure.repository",
        "erp.modules.audit.infrastructure.repository",
        "erp.modules.settings.infrastructure.repository",
        "erp.shared.infrastructure.database",
    ]
    for mod_name in infrastructure_modules:
        __import__(mod_name)
