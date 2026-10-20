# Guia de Instalação para Desenvolvedores

## Pré-requisitos

- Python 3.12+
- uv (gerenciador de pacotes)
- Git
- SQLite3 (incluído no Python)
- Qt6 (via PySide6 - instalado automaticamente)

## Configuração do Ambiente de Desenvolvimento

### 1. Clone e Instalação

```bash
git clone https://github.com/ivanmamedio/NexoERP.git
cd NexoERP

# Instalar uv se não tiver
pip install uv

# Instalar todas as dependências (dev, build, test)
uv sync --all-groups --dev
```

### 2. Configurar Variáveis de Ambiente (Opcional)

```bash
# Copiar template
cp .env.example .env 2>/dev/null || true

# Editar se necessário
# NEXOERP_ADMIN_PASSWORD=admin123
# NEXOERP_ADMIN_USERNAME=admin
# NEXOERP_DATA_DIR=~/.local/share/NexoERP
# NEXOERP_BACKUP_SECONDARY=/mnt/backup/NexoERP
```

### 3. Executar Testes

```bash
# Todos os testes
uv run pytest

# Testes específicos
uv run pytest tests/unit/modules/identity/
uv run pytest tests/integration/test_bootstrap.py

# Com cobertura
uv run pytest --cov=src/erp --cov-report=html
```

### 4. Verificações de Qualidade

```bash
# Lint
uv run ruff check .

# Type checking
uv run mypy src/erp

# Import linting
uv run python -m importlinter  # se instalado
```

### 5. Executar a Aplicação

```bash
# Modo normal (com UI)
uv run python -m erp

# Modo headless (sem display, apenas bootstrap)
# Linux:
DISPLAY="" uv run python -m erp
# Windows PowerShell:
$env:DISPLAY=""; uv run python -m erp
```

## Estrutura do Projeto

```
NexoERP/
├── src/
│   └── erp/
│       ├── modules/
│       │   ├── identity/        # Usuários, papéis, login
│       │   ├── companies/       # Empresas multi-tenant
│       │   ├── catalog/         # Produtos, categorias, estoque
│       │   ├── pricing/         # Calculadora de preços
│       │   ├── cash/            # Caixa, sessões, sangria
│       │   ├── sales/           # Vendas, PDV, pagamentos
│       │   ├── treasury/        # Financeiro, contas a pagar/receber
│       │   ├── audit/           # Auditoria, logs
│       │   ├── receipts/        # Recibos, impressão
│       │   ├── backup/          # Backup automático
│       │   ├── reports/         # Relatórios (CSV/PDF)
│       │   └── fiscal/          # Interface fiscal (Protocol)
│       ├── shared/
│       │   ├── domain/          # Entidades base, Money
│       │   ├── application/     # EventBus, casos de uso base
│       │   ├── infrastructure/  # DB, migrações, repositórios base
│       │   ├── ui/              # Componentes Qt base
│       │   ├── exceptions/      # Tratamento global de exceções
│       │   └── security_audit.py # Auditoria de segurança
│       └── bootstrap.py         # Composition root
├── tests/
│   ├── unit/                    # Testes unitários por módulo
│   ├── integration/             # Testes de integração
│   └── security/                # Testes de segurança
├── scripts/
│   └── load_perf_data.py        # Carga de dados para performance
├── docs/
│   └── user_guide.md            # Manual do usuário
├── alembic.ini                  # Configuração de migrações
├── pyproject.toml               # Configuração do projeto
└── README.md
```

## Migrações de Banco de Dados

### Ver Status
```bash
uv run alembic -c alembic.ini current
uv run alembic -c alembic.ini history
```

### Criar Nova Migração
```bash
uv run alembic -c alembic.ini revision -m "descrição da mudança"
# Editar o arquivo gerado em src/erp/shared/infrastructure/database/alembic/versions/
```

### Aplicar Migrações
```bash
# Em desenvolvimento (usa banco de dados local)
uv run alembic -c alembic.ini upgrade head

# Em produção (aplicação faz automaticamente no bootstrap)
```

### Testar Migração N-1 para N
```bash
uv run pytest tests/security/test_security_audit.py::TestSecurityAudit::test_migration_n_minus_1_to_n -v
```

## Empacotamento (Build)

### Linux (.deb + AppImage)
```bash
# Instalar dependências de build
uv sync --group build

# Build onedir (sai em dist/ERP/)
uv run pyinstaller packaging/pyinstaller.spec

# .deb com nfpm
VERSION=0.1.0
sed "s/__VERSION__/${VERSION}/" packaging/linux/nfpm.yaml > /tmp/nfpm.yaml
nfpm package --config /tmp/nfpm.yaml --packager deb --target dist/nexoerp-${VERSION}-amd64.deb

# AppImage
mkdir -p AppDir/usr/bin
cp -r dist/ERP/* AppDir/usr/bin/
cp packaging/linux/erp.desktop AppDir/
cp packaging/linux/icons/erp.png AppDir/
printf '#!/bin/sh\nexec "$(dirname "$0")/usr/bin/ERP" "$@"' > AppDir/AppRun
chmod +x AppDir/AppRun
./appimagetool AppDir nexoerp-${VERSION}-x86_64.AppImage
```

### Windows (Inno Setup)
```powershell
# Build onedir
uv run pyinstaller packaging/pyinstaller.spec --distpath dist/windows-latest

# Gerar instalador
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows\installer.iss
# Saída: dist/windows/NexoERP-Setup.exe
```

## CI/CD

O pipeline roda automaticamente no GitHub Actions:
- `.github/workflows/ci.yml` - lint, type-check, import-linter, testes (Ubuntu + Windows)
- `.github/workflows/release.yml` - build e release em tags `v*`

## Convenções de Código

### Arquitetura Clean Architecture
- **Domain:** Entidades puras, sem dependências externas
- **Application:** Casos de uso, ports (interfaces)
- **Infrastructure:** Implementações concretas (SQLAlchemy, Qt)
- **Presentation:** Widgets, dialogs, presenters

### Regras de Dependência
- Domain não importa nada de fora
- Application importa apenas Domain e shared
- Infrastructure implementa ports do Application
- Presentation usa Application e shared.ui
- **NUNCA** importe infrastructure/presentation de outro módulo

### Naming
- Entidades: `PascalCase` (ex: `Product`, `Sale`)
- Value Objects: `PascalCase` (ex: `Money`, `ReportFilter`)
- Casos de Uso: `VerbNoun` (ex: `CreateProduct`, `FinalizeSale`)
- Ports: `NounPort` (ex: `ProductRepositoryPort`)
- Repositórios: `SqlAlchemyNounRepository`

### Testes
- Unitários: `tests/unit/modules/<module>/test_<action>.py`
- Integração: `tests/integration/test_<feature>.py`
- Segurança: `tests/security/test_<audit>.py`
- Use `pytest-qt` para testes de UI

### Type Hints
- Sempre use type hints completos
- `from __future__ import annotations` em todos os arquivos
- Use `X | Y` em vez de `Union[X, Y]`
- Use `collections.abc.Sequence` em vez de `typing.Sequence`

## Debugging

### Logs
```bash
# Ver logs de erro
uv run python -c "
from erp.config.paths import get_data_dir
import sqlite3
conn = sqlite3.connect(get_data_dir() / 'erp.db')
for row in conn.execute('SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10'):
    print(row)
"
```

### Debug do PDV
```bash
# Testes do presenter do PDV
uv run pytest tests/unit/modules/sales/test_pos_presenter.py -v -s
```

### Banco de Dados
```bash
# Abrir shell SQLite
sqlite3 ~/.local/share/NexoERP/erp.db

# Ver tabelas
.tables

# Ver schema
.schema products
```

## Contribuindo

1. Fork o repositório
2. Crie branch: `git checkout -b feat/nova-funcionalidade`
3. Commit: `git commit -m "feat(module): descrição"`
4. Push: `git push origin feat/nova-funcionalidade`
5. Abra Pull Request

### Padrão de Commits
```
feat(module): descrição curta
fix(module): correção
refactor(module): refatoração
docs: documentação
test: testes
chore: manutenção
```

---

**Dúvidas?** Abra uma issue ou consulte o README.md