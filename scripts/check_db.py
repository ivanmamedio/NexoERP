#!/usr/bin/env python3
"""Verifica estado do banco de dados."""
from pathlib import Path
from sqlalchemy import create_engine, text
from erp.config.paths import get_data_dir

db_path = get_data_dir() / "erp.db"
print(f"Banco: {db_path}")
engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
with engine.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
    print(f"Tabelas ({len(tables)}):")
    for t in tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM [{t[0]}]")).scalar()
        print(f"  - {t[0]}: {count} rows")

    # Verifica índices
    indexes = conn.execute(text("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name, name")).fetchall()
    print(f"\nÍndices ({len(indexes)}):")
    for idx in indexes:
        print(f"  - {idx[1]}: {idx[0]}")
