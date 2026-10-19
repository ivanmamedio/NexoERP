# Relatório de Auditoria — NexoERP

**Data:** 18/10/2026  
**Versão analisada:** Commit `78ea756` (HEAD → main)  
**Ambiente:** Python 3.12.15, Linux, PySide6 6.12.0, SQLite 3, SQLAlchemy 2.x  

---

## 1. Resumo Executivo

O projeto NexoERP apresenta uma base arquitetural sólida seguindo Clean Architecture com monólito modular, mas **existem falhas críticas que impedem a execução correta da aplicação e dos testes**. Os principais problemas são:

| Categoria | Quantidade | Severidade |
|-----------|------------|------------|
| Testes falhando | 5 | **P0 — Crítico** |
| Violações de arquitetura (import-linter) | 3 contratos quebrados | **P1 — Alto** |
| Formatação inconsistente (Ruff) | 92 arquivos | **P2 — Médio** |
| Discrepância documentação vs código | Múltiplas | **P2 — Médio** |
| Problema de DDL no bootstrap | 1 | **P0 — Crítico** |
| Arquivo snapshot redundante | 1 | **P3 — Baixo** |

**Estado geral:** O código compila e `mypy` passa em modo strict, mas a aplicação **não inicia corretamente** (falha no bootstrap) e a suíte de testes **não passa completamente**.

---

## 2. Problemas Confirmados

### 2.1 P0 — Falha no Bootstrap / Inicialização do Banco (Crítico)

**Arquivo:** `src/erp/modules/audit/infrastructure/triggers.py:60`  
**Função:** `install_triggers()`  

**Evidência:**
```python
_BYPASS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS audit_bypass (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO audit_bypass (id, enabled) VALUES (1, 0);
"""
```
```python
connection.execute(text(_BYPASS_TABLE_DDL))  # Executa DUAS statements de uma vez
```

**Erro:** `sqlite3.ProgrammingError: You can only execute one statement at a time.`

**Impacto:** 
- `bootstrap()` falha sempre → aplicação não inicia
- 2 testes de integração falham (`test_bootstrap_creates_db_with_required_pragmas`, `test_bootstrap_is_idempotent`)
- Qualquer tentativa de criar o banco do zero falha

**Causa raiz:** SQLite (via `pysqlite`/`sqlite3` stdlib) **não suporta múltiplas statements em uma única chamada `execute()`**. O DDL contém `CREATE TABLE` + `INSERT` no mesmo string.

**Correção recomendada:** Separar em duas chamadas `execute()` ou usar `executescript()` (se disponível) ou executar cada statement individualmente.

---

### 2.2 P0 — Testes de Autenticação Quebrados (Crítico)

**Arquivos afetados:**
- `tests/unit/modules/identity/test_login_presenter.py` (2 testes)
- `tests/ui/test_login.py` (1 teste)

**Evidência:**
```python
# AuthenticateOutput agora exige company_id (src/erp/modules/identity/application/authenticate.py:20)
@dataclass(slots=True, frozen=True)
class AuthenticateOutput:
    user_id: int
    username: str
    company_id: int | None  # NOVO CAMPO OBRIGATÓRIO
    must_change_password: bool
```

**Testes mockam `AuthenticateOutput` sem `company_id`:**
```python
# tests/unit/modules/identity/test_login_presenter.py:25
return AuthenticateOutput(
    user_id=self.return_user_id,
    username=self.return_username,
    must_change_password=self.must_change_password,  # FALTA company_id
)
```

**Erro:** `TypeError: AuthenticateOutput.__init__() missing 1 required positional argument: 'company_id'`

**Impacto:** 3 testes de autenticação falham (unit + UI)

**Correção recomendada:** Atualizar todos os mocks/fakes nos testes para incluir `company_id=None` (ou valor apropriado).

---

### 2.3 P1 — Violações de Arquitetura (import-linter) — 3 Contratos Quebrados

**Configuração:** `.importlinter` define contrato `modules-independent` (independência entre módulos)

| Módulo Origem | Módulo Destino | Tipo de Importação | Linhas |
|---------------|----------------|-------------------|--------|
| `erp.modules.companies` | `erp.modules.identity` | `domain.user` + `application.ports` | `permission_gate.py:5-6` |
| `erp.modules.sales` | `erp.modules.catalog` | `application.ports` + `infrastructure.unit_of_work` | `add_item.py:5`, `services.py:7-9` |
| `erp.modules.pricing` | `erp.modules.catalog` | `application.services` + `application.update_price` | `services.py:7-8` |

**Evidência — companies/permission_gate.py:**
```python
from erp.modules.identity.application.ports import UserRepository  # VIOLAÇÃO
from erp.modules.identity.domain.user import User  # VIOLAÇÃO
```

**Evidência — sales/services.py:**
```python
from erp.modules.catalog.infrastructure.unit_of_work import SqlAlchemyCatalogUnitOfWork  # VIOLAÇÃO GRAVE: importa infrastructure!
```

**Impacto:** 
- Quebra da regra "um módulo só importa API pública `application` de outro módulo"
- Sales importa **infrastructure** do Catalog (violação severa de Clean Architecture)
- Acoplamento que dificulta testes, manutenção e evolução independente

**Correção recomendada:**
1. **Companies → Identity:** Criar port/interface em `companies.application.ports` para verificar permissões, injetar implementação no bootstrap
2. **Sales → Catalog:** Usar apenas `catalog.application.ports.ProductRepository` (já faz em `add_item.py`), remover import de `SqlAlchemyCatalogUnitOfWork` do `services.py` — passar `catalog_uow` como dependência injetada
3. **Pricing → Catalog:** Mesmo padrão — depender apenas de ports, não de services/concrete classes

---

### 2.4 P2 — Formatação Inconsistente (Ruff) — 92 Arquivos

**Comando:** `uv run ruff format --check .` → 92 arquivos seriam reformatados

**Exemplos de problemas:**
- Linhas longas não quebradas (ex: `src/erp/modules/cash/application/open_cash_session.py:50`)
- Espaçamento inconsistente em imports (`from __future__ import annotations` sem linha em branco após)
- Parênteses desnecessários ou faltando em chamadas de função
- Listas/dicionários com formatação inconsistente

**Impacto:** Ruído em diffs, dificulta code review, viola padrão do projeto

**Correção:** `uv run ruff format .` (aplicar formatação automática)

---

### 2.5 P2 — Inconsistência no Tratamento de Datetime (created_at/updated_at)

**Dois padrões diferentes coexistem:**

**Padrão A — Shared models (`src/erp/shared/infrastructure/database/models.py`):**
```python
class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False  # SQL expression
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

**Padrão B — Module models (ex: `identity/infrastructure/models.py`):**
```python
def _utcnow() -> datetime:
    return datetime.now(UTC)

created_at: Mapped[datetime] = mapped_column(
    UTCDateTime, default=_utcnow, nullable=False  # Python callable
)
updated_at: Mapped[datetime] = mapped_column(
    UTCDateTime, default=_utcnow, onupdate=_utcnow, nullable=False
)
```

**Problemas:**
1. **Inconsistência semântica:** `server_default=func.now()` usa relógio do banco; `default=_utcnow` usa relógio da aplicação
2. **Timezone:** `func.now()` do SQLite retorna datetime **naive** (sem timezone); `UTCDateTime` espera aware → pode causar erros silenciosos
3. **`onupdate=_utcnow`:** Funciona como callable no SQLAlchemy, mas `server_default=func.now()` + `onupdate=func.now()` no mixin não garante timezone UTC

**Risco:** Divergência de timestamps entre tabelas, bugs de ordenação, problemas de auditoria/lockout

**Recomendação:** Padronizar em **uma única abordagem** (recomendado: Python callable `_utcnow` + `UTCDateTime` type para garantir timezone aware consistente). Remover `TimestampMixin` ou adaptar para usar `UTCDateTime`.

---

### 2.6 P2 — Discrepância Documentação vs Implementação (README.md)

**README.md (linhas 141-149) afirma:**

| Módulo | Status no README |
|--------|------------------|
| Catálogo, Estoque, Caixa, Vendas, Tesouraria | **Não implementados** |
| Auditoria, Backup, Relatórios | **Não implementados** |

**Realidade no código (`src/erp/modules/`):**
- ✅ `catalog/` — Completo (domain, application, infrastructure, presentation)
- ✅ `cash/` — Completo (sessions, sangria, suprimento, fechamento)
- ✅ `sales/` — Completo (StartSale, AddItem, FinalizeSale, ApplyDiscount, CancelSale/CancelItem)
- ✅ `treasury/` — Implementado (financial_entries, subscribers)
- ✅ `audit/` — Implementado (audit_logs, triggers, subscriber, view)
- ⚠️ `backup/` — Apenas estrutura (vazio)
- ⚠️ `reports/` — Não existe
- ⚠️ `receipts/` — Não existe
- ✅ `fiscal/` — Apenas interface `FiscalPort` (conforme espec)

**Impacto:** Documentação engana desenvolvedores e usuários sobre estado real do projeto

**Correção:** Atualizar tabela de status no README para refletir implementação real

---

### 2.7 P2 — Discrepância Roadmap vs Implementação (Stack/OS)

**Roadmap_ERP_Pequenos_Comercios_Windows7_Debian.md:**
- **Windows 7** como prioridade
- **Python 3.8** + **PyQt5/Qt 5** para Windows 7
- Builds separados por SO

**Implementação real (pyproject.toml + código):**
- **Python 3.12+** (requerido)
- **PySide6/Qt 6** (não roda no Windows 7)
- **Windows 10+** e Linux (conforme README)
- Build único multiplataforma

**Impacto:** Documentação do roadmap **não reflete a realidade técnica** — decisões arquiteturais foram tomadas (PySide6, Python 3.12) mas roadmap não foi atualizado

**Recomendação:** Atualizar roadmap ou criar documento `ARCHITECTURE_DECISIONS.md` registrando as decisões reais e por que Windows 7 foi descartado

---

### 2.8 P3 — Arquivo Snapshot Redundante: `codigo_para_analise.md`

**Arquivo:** `codigo_para_analise.md` (1.289 linhas)

**Conteúdo:** Snapshot gerado de múltiplos arquivos do projeto (pyproject.toml, alembic.ini, models, migrations, etc.)

**Análise:**
- ✅ É snapshot gerado (provavelmente por ferramenta de IA/análise)
- ✅ Duplica código já presente no repositório
- ✅ Conteúdo **desatualizado** (ex: mostra migrações antigas, não reflete estado atual)
- ❌ Nenhum workflow, documentação ou ferramenta depende dele
- ❌ Cria confusão sobre qual código é autoritativo

**Classificação:** **SAFE TO REMOVE**

**Recomendação:** Remover do repositório. Se necessário para análise de IA, regenerar sob demanda ou adicionar ao `.gitignore`

---

### 2.9 P3 — Migrations: `0001_initial` Vazia

**Arquivo:** `src/erp/shared/infrastructure/database/alembic/versions/0001_initial.py`

```python
def upgrade() -> None:
    """Baseline: nothing to create."""
```

**Problema:** Migração baseline vazia que não cria tabelas. A primeira migração real é `0002_identity_tables`. Isso funciona mas é atípico — Alembic normalmente espera que a primeira migração crie o schema inicial.

**Impacto:** Baixo (funciona), mas confuso para novos desenvolvedores

**Recomendação:** Manter (não reescrever migrações históricas), mas documentar no README/CHANGELOG

---

### 2.10 P3 — Import-linter: Módulos Faltando no Contrato

**Contrato `modules-independent` lista:** audit, backup, cash, catalog, companies, fiscal, identity, pricing, receipts, reports, sales, treasury

**Módulos existentes NÃO listados:** `backup`, `fiscal`, `receipts`, `reports` (existem em `src/erp/modules/` mas estão vazios ou só com `__init__.py`)

**Impacto:** Import-linter não valida isolamento desses módulos (embora vazios, podem crescer)

**Recomendação:** Adicionar ao contrato ou remover pastas vazias se não forem usadas

---

## 3. Problemas Anteriores — Status

| Problema Reportado Anteriormente | Status Atual | Evidência |
|----------------------------------|--------------|-----------|
| Datetime imports/UTC handling | **Parcialmente resolvido** | Usa `UTCDateTime` + `_utcnow()` callable (correto), mas `TimestampMixin` usa `func.now()` inconsistente |
| Undefined symbols/association tables | **Resolvido** | Models importam corretamente, relationships funcionam |
| SQLAlchemy model typing errors | **Resolvido** | `mypy strict` passa sem erros |
| ORM relationships incorretas | **Resolvido** | `back_populates` coerentes, FKs definidas |
| Migration/schema inconsistencies | **Parcial** | Migrações aplicam, mas `install_triggers` quebra bootstrap |
| Identity/RBAC defects | **Parcial** | Lógica correta, mas testes quebrados por `company_id` faltando |
| Import errors/circular deps | **Parcial** | Sem erros de import runtime, mas import-linter flagra violações arquiteturais |
| Ruff violations | **Pendente** | 92 arquivos fora de formatação |
| mypy strict violations | **Resolvido** | `mypy` passa limpo |
| Test collection/execution failures | **Pendente** | 5 testes falhando (2 bootstrap + 3 auth) |
| Bootstrap/db init failures | **Pendente** | Falha crítica no `install_triggers` |
| Incomplete/misleading docs | **Pendente** | README e Roadmap desatualizados |

---

## 4. Arquivos Desnecessários / Candidatos a Limpeza

| Arquivo/Pasta | Classificação | Justificativa | Validação Necessária |
|---------------|---------------|---------------|---------------------|
| `codigo_para_analise.md` | **SAFE TO REMOVE** | Snapshot redundante, desatualizado, nada depende dele | Confirmar que nenhum script/CI usa |
| `src/erp/modules/backup/` | **INVESTIGATE** | Pasta vazia (só `__init__.py` ×4) — placeholder fase 4 | Verificar roadmap: fase 4 planejada |
| `src/erp/modules/fiscal/` | **KEEP** | Interface `FiscalPort` existe — extension point válido | Manter como contrato futuro |
| `src/erp/modules/receipts/` | **INVESTIGATE** | Pasta vazia — fase 2.4 planejada | Verificar se será implementado |
| `src/erp/modules/reports/` | **INVESTIGATE** | Não existe — fase 4 planejada | Verificar roadmap |
| `build/`, `dist/` | **KEEP (gitignored)** | Artefatos de build local, já no `.gitignore` | Nenhuma ação necessária |
| `__pycache__/`, `*.pyc` | **KEEP (gitignored)** | Artefatos de build, já no `.gitignore` | Nenhuma ação necessária |

**Nota:** Não remover módulos vazios planejados no roadmap (backup, receipts, reports) — são extension points legítimos.

---

## 5. Melhorias Implementadas (Já no Código)

O código já incorpora boas práticas:
- ✅ Clean Architecture respeitada na estrutura de pastas
- ✅ `Money` value object (centavos, int, sem float)
- ✅ `Quantity` em milésimos (int)
- ✅ Unit of Work pattern com `SqlAlchemyUnitOfWork`
- ✅ EventBus síncrono tipado para desacoplamento
- ✅ RBAC com permissões granulares verificadas no use-case
- ✅ Auditoria com hash encadeado + triggers SQLite
- ✅ Multi-empresa via `company_id` + `CurrentSession`
- ✅ Seed idempotente de roles/permissions + admin inicial
- ✅ Password policy + lockout após 5 tentativas (bcrypt)
- ✅ `mypy strict` passando
- ✅ `ruff` lint passando (sem erros, só formatação)
- ✅ Testes unitários e integração abrangentes (155/160 passando)

---

## 6. Testes — Resultados Atuais

```bash
# Comandos executados
uv run pytest -v              # 155 passed, 5 failed
uv run ruff check .           # 0 issues (lint OK)
uv run ruff format --check .  # 92 files would be reformatted
uv run mypy                   # Success: no issues found in 213 source files
uv run import-linter lint     # 1 broken contract (3 module pairs)
```

### Detalhamento das Falhas

| Teste | Tipo | Erro | Causa Raiz |
|-------|------|------|------------|
| `test_bootstrap_creates_db_with_required_pragmas` | Integration | `sqlite3.ProgrammingError: You can only execute one statement at a time` | `_BYPASS_TABLE_DDL` tem 2 statements |
| `test_bootstrap_is_idempotent` | Integration | Mesmo erro acima | Mesmo |
| `test_login_presenter_success` | Unit | `TypeError: missing 'company_id'` | Mock não atualizado |
| `test_login_presenter_sets_must_change_password` | Unit | `TypeError: missing 'company_id'` | Mock não atualizado |
| `test_login_dialog_authenticates` | UI (pytest-qt) | `TypeError: missing 'company_id'` | Mock não atualizado |

**Testes não executados:** Nenhum (todos coletados)

---

## 7. Segurança e Integridade

### Vulnerabilidades Verificadas

| Item | Status | Observação |
|------|--------|------------|
| Senhas em plaintext | ✅ Seguro | bcrypt com hash, nunca logadas |
| Hash exposto em logs | ✅ Seguro | Logs não incluem `password_hash` |
| SQL Injection | ✅ Seguro | SQLAlchemy ORM + queries parametrizadas |
| Path traversal | ✅ Seguro | `platformdirs` para paths, sem input usuário direto |
| Lockout bypass | ⚠️ Verificar | `locked_until` usa `datetime.now(UTC)` — OK, mas testar edge cases |
| Admin default password | ✅ Seguro | Não há senha padrão; `create_first_admin` exige env var |
| Multi-company isolation | ⚠️ Parcial | `company_id` nas tabelas, mas `CompanyPermissionGate` importa `identity` violando arquitetura |

### Riscos Remanescentes
1. **Bootstrap falha** → app não roda em produção (P0)
2. **Triggers de auditoria** podem bloquear operações legítimas se bypass falhar
3. **Timezone inconsistency** entre `func.now()` (naive) e `UTCDateTime` (aware) → possíveis bugs silenciosos
4. **Acoplamento Sales→Catalog infrastructure** quebra isolamento transacional

---

## 8. Compatibilidade

| Plataforma | Suportada no Código | Testada | Observação |
|------------|---------------------|---------|------------|
| Linux (Debian/Ubuntu) | ✅ Sim | ✅ CI (ubuntu-22.04) | Funciona |
| Windows 10+ | ✅ Sim (README) | ❓ CI (windows-latest) | PySide6 requer Windows 10+ |
| Windows 7 | ❌ Não (PySide6) | ❌ Não testado | Roadmap desatualizado |
| Python 3.12 | ✅ Sim | ✅ | Requerido no pyproject.toml |
| Python 3.8 | ❌ Não | ❌ | Roadmap menciona mas código usa 3.12+ |

**Limitação do ambiente atual:** Não foi possível testar build Windows ou empacotamento (.deb, AppImage, Inno Setup) — apenas validação de código e testes unitários/integração em Linux.

---

## 9. Pendências — Decisões Requerendo Aprovação

| Item | Decisão Necessária | Opções |
|------|-------------------|--------|
| **Arquitetura: Sales → Catalog** | Como desacoplar? | A) Injetar `CatalogUnitOfWork` via bootstrap (recomendado) / B) Criar port `CatalogUnitOfWorkPort` em sales.application.ports |
| **Arquitetura: Companies → Identity** | Como verificar permissão? | A) Port `PermissionChecker` em companies / B) Mover gate para shared/application |
| **Datetime strategy** | Unificar `server_default=func.now()` vs `default=_utcnow()` | A) Padronizar em Python callable + UTCDateType (recomendado) / B) Usar `server_default` everywhere com timezone hack |
| **Windows 7 support** | Manter no roadmap ou remover? | A) Remover do roadmap (já decidido implicitamente) / B) Criar branch legacy com PyQt5 |
| **README status table** | Atualizar para refletir realidade? | Sim — atualizar para "Implementado" onde aplicável |

---

## 10. Próximos Passos Recomendados (Prioridade)

### Imediato (P0 — Bloqueiam execução)
1. **Corrigir `install_triggers()`** — separar DDL em múltiplos `execute()` → desbloqueia bootstrap e 2 testes
2. **Atualizar mocks de `AuthenticateOutput`** — adicionar `company_id=None` em 3 arquivos de teste → desbloqueia 3 testes

### Curto Prazo (P1 — Arquitetura)
3. **Resolver violações import-linter** — refatorar `companies.permission_gate`, `sales.services`, `pricing.services` para depender apenas de ports
4. **Aplicar `ruff format .`** — padronizar 92 arquivos

### Médio Prazo (P2 — Qualidade)
5. **Unificar estratégia datetime** — remover `TimestampMixin` ou adaptar para `UTCDateTime`
6. **Atualizar README.md** — tabela de status dos módulos
7. **Atualizar/Arquivar Roadmap** — documentar decisões reais (PySide6, Python 3.12, Windows 10+)

### Baixa Prioridade (P3 — Limpeza)
8. **Remover `codigo_para_analise.md`**
9. **Avaliar módulos vazios** (backup, receipts, reports) — manter ou remover pastas

---

## 11. Resumo Git

```
## Modified files (unstaged, user changes):
 M tests/integration/modules/cash/test_repository.py
 M tests/integration/modules/catalog/test_repository.py
 M tests/integration/modules/sales/test_repository.py
 M tests/unit/modules/cash/test_close_cash_session.py
 M tests/unit/modules/cash/test_open_cash_session.py
 M tests/unit/modules/cash/test_register_sangria.py
 M tests/unit/modules/catalog/test_update_price.py
 M tests/unit/modules/companies/test_get_company.py
 M tests/unit/modules/companies/test_list_companies.py
 M tests/unit/modules/pricing/test_calculator.py

## Untracked files:
 ?? AUDITORIA_RELATORIO.md        (este relatório)
 ?? codigo_para_analise.md        (candidato a remoção)
 ?? prompt_correções.md           (prompt original)

## Build artifacts (gitignored):
 build/
 dist/
```

**Nenhum commit foi feito.** Todas as alterações acima são do usuário (testes modificados) ou arquivos novos. O relatório não modifica nenhum arquivo fonte.

---

## 12. Aprovação Necessária

Antes de prosseguir para **Stage B (Change Plan)** e **Stage C (Safe Corrections)**, preciso da sua autorização para:

1. **Correções P0** (bootstrap + testes auth) — **baixo risco, alto impacto**
2. **Refatoração arquitetural P1** (import-linter) — **médio risco, requer design de ports**
3. **Formatação P2** (ruff format) — **baixo risco, apenas estilo**
4. **Limpeza P3** (codigo_para_analise.md) — **baixo risco**

Por favor, revise este relatório e indique:
- Quais correções autoriza agora
- Quais decisões arquiteturais (P1) prefere discutir antes
- Se deseja que eu proponha um **Change Plan detalhado** para cada item aprovado

---

*Relatório gerado em conformidade com as fases 1-13 do prompt de auditoria. Nenhum arquivo foi modificado durante esta análise.*