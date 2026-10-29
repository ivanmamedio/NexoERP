# -*- mode: python ; coding: utf-8 -*-
# NexoERP PyInstaller spec — modo onedir (Fase 0).
# Caminhos resolvidos via SPEC para funcionar de qualquer diretório de trabalho.

import os

from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
ROOT_DIR = os.path.dirname(SPEC_DIR)
SRC_DIR = os.path.join(ROOT_DIR, "src")
DB_DIR = os.path.join(SRC_DIR, "erp", "shared", "infrastructure", "database")
LOGO_PATH = os.path.join(SRC_DIR, "erp", "ui", "resources", "logo.png")

# Falha clara se o logo não existir antes de iniciar o build.
if not os.path.isfile(LOGO_PATH):
    raise SystemExit(
        f"Arquivo de logo não encontrado: {LOGO_PATH}. "
        "Informe o caminho correto ou adicione o arquivo antes de buildar."
    )

a = Analysis(
    [os.path.join(SRC_DIR, "erp", "__main__.py")],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[
        (
            os.path.join(DB_DIR, "alembic"),
            "erp/shared/infrastructure/database/alembic",
        ),
        (LOGO_PATH, "erp/ui/resources"),
    ],
    hiddenimports=collect_submodules("erp") + collect_submodules("sqlalchemy"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["sqlalchemy.ext.asyncio"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ERP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, "packaging", "windows", "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ERP",
)
