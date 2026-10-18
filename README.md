# ERP

ERP desktop offline-first para pequenos comércios.

## Stack alvo

- Python 3.12+
- PySide6 (Qt Widgets)
- SQLite (WAL, foreign_keys=ON)
- SQLAlchemy 2.0
- Alembic (migrações)
- bcrypt
- platformdirs
- pytest, pytest-qt
- Ruff, mypy (strict), import-linter
- uv

## Compatibilidade

- **Windows 10+** e **Linux** (baseado em Debian/Ubuntu)
- Python 3.12 e PySide6 são os requisitos mínimos
- Windows 7 não é suportado nesta etapa (requeriria PyQt5/Qt 5 e Python 3.8, tratamento como plataforma legada futura)

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/ivanmamedio/NexoERP.git
cd NexoERP

# Criar e ativar ambiente virtual com uv
uv sync --all-groups --dev
source .venv/bin/activate
```

## Execução

```bash
# Executar a aplicação
uv run python -m erp

# Em ambiente headless (sem DISPLAY), o bootstrap roda e a UI não inicia
uv run python -m erp
```

## Testes

```bash
# Executar todos os testes
uv run pytest

# Executar testes de identidade
uv run pytest tests/unit/modules/identity/ tests/integration/modules/identity/

# Executar teste de bootstrap
uv run pytest tests/integration/test_bootstrap.py
```

## Verificações de qualidade

```bash
# Lint
uv run ruff check .

# Type checking
uv run mypy

# Import linting
uv run import-linter lint
```

## Build e empacotamento

### Testar o build do PyInstaller localmente

```bash
# 1. Instalar o grupo de dependencias de build (PyInstaller)
uv sync --group build

# 2. Gerar o build onedir (sai em dist/ERP/ERP + dist/ERP/_internal/)
uv run pyinstaller packaging/pyinstaller.spec

# 3. Executar o binario empacotado
./dist/ERP/ERP                # Linux
dist\ERP\ERP.exe              # Windows

# 3b. Smoke test headless (sem UI): valida bootstrap + migracoes no bundle
env -u DISPLAY XDG_DATA_HOME=/tmp/erp-frozen-test ./dist/ERP/ERP
# Esperado: exit code 0 e banco criado em /tmp/erp-frozen-test/NexoERP/erp.db
# (o app detecta ausencia de DISPLAY, roda o bootstrap e sai sem abrir janela)
```

O mesmo comando serve para validar após qualquer alteração de dependência.
Se o bundle falhar com "Database migration failed", verifique se o
diretório `alembic/` está presente em `dist/ERP/_internal/erp/shared/infrastructure/database/`
(incluído via `datas` no `packaging/pyinstaller.spec`).

### Gerar pacotes Linux (AppImage e .deb) localmente

```bash
# Build na mesma estrutura usada pelo CI
uv run pyinstaller packaging/pyinstaller.spec --distpath dist/ubuntu-22.04

# .deb com nfpm (baixar o binario em https://github.com/goreleaser/nfpm/releases)
VERSION=0.1.0
sed "s/__VERSION__/${VERSION}/" packaging/linux/nfpm.yaml > /tmp/nfpm.rendered.yaml
nfpm package --config /tmp/nfpm.rendered.yaml --packager deb --target dist/nexoerp-${VERSION}-amd64.deb

# AppImage (baixar appimagetool em https://github.com/AppImage/AppImageKit/releases)
mkdir -p AppDir/usr/bin
cp -r dist/ubuntu-22.04/ERP/* AppDir/usr/bin/
cp packaging/linux/erp.desktop AppDir/erp.desktop
cp packaging/linux/icons/erp.png AppDir/erp.png
printf '%s\n' '#!/bin/sh' 'exec "$(dirname "$0")/usr/bin/ERP" "$@"' > AppDir/AppRun
chmod +x AppDir/AppRun
./appimagetool AppDir nexoerp-${VERSION}-x86_64.AppImage
```

### Instalador Windows

```powershell
# Requer Inno Setup 6 e o build gerado com --distpath dist/windows-latest
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows\installer.iss
# Saida: dist/windows/NexoERP-Setup.exe
```

### CI

- `.github/workflows/ci.yml` — ruff, mypy, import-linter e pytest em `ubuntu-22.04` e `windows-latest` (push/PR para `main`).
- `.github/workflows/release.yml` — dispara em tag `v*`, gera `.exe` (Inno Setup), AppImage e `.deb`, e publica no GitHub Releases.

## Limitações conhecidas

1. **Windows 7 não é suportado** nesta versão. O roadmap previa investigação de PyQt5/Qt 5 e Python 3.8 para Windows 7, mas a decisão atual é priorizar Windows 10+ e Linux com Python 3.12 e PySide6.
2. **Módulo fiscal não implementado.** Existe apenas uma interface vazia `FiscalPort`. Não há emissão de documentos fiscais.
3. **Primeiro administrador:** não há senha padrão. Use `create_first_admin()` com credenciais explícitas via `NEXOERP_ADMIN_PASSWORD` ou chame diretamente no código.
4. **Backup e restauração:** módulo em desenvolvimento (Fase 4 do roadmap).

## Estado real das funcionalidades

| Módulo | Status |
|--------|--------|
| Identity (usuários, papéis, permissões) | Implementado (domínio, aplicação, infraestrutura) |
| Bootstrap (inicialização, banco, migrations) | Implementado |
| Banco de dados (SQLite WAL, PRAGMAs) | Implementado |
| Migrações Alembic | Implementadas (0001_initial, 0002_identity_tables) |
| Empacotamento (PyInstaller, .deb, Inno Setup) | Configurado |
| Catálogo, Estoque, Caixa, Vendas, Tesouraria | Não implementados |
| Auditoria, Backup, Relatórios | Não implementados |
| Interface gráfica (PySide6) | Janela principal básica |
