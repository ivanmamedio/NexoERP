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

```bash
# Build com PyInstaller
uv run pyinstaller packaging/pyinstaller.spec --distpath dist/linux

# Pacote .deb (Linux)
./nfpm package --target dist/nexoerp-v0.1.0-amd64.deb --packager deb -f packaging/linux/nfpm.yaml

# Instalador Windows (apenas no Windows)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging/windows/installer.iss
```

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
