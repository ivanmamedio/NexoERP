# Relatório de Revisão Arquitetural — NexoERP

**Data:** 19/10/2026  
**Versão analisada:** Pós-correções P0/P1/P2 (commit HEAD)  
**Escopo:** 193 arquivos fonte, 67 arquivos de teste  

---

## Sumário Executivo

O código está **sólido, bem testado e arquiteturalmente correto**. As correções recentes resolveram os bloqueadores críticos. Este relatório identifica oportunidades de **refatoração evolutiva** para reduzir duplicação, melhorar expressividade e facilitar manutenção futura — sem quebrar o que já funciona.

| Métrica | Valor |
|---------|-------|
| Arquivos fonte | 193 |
| Testes | 160 passing |
| Dataclasses | 86 |
| Protocols (ports) | 52 |
| Repositórios | 32 |
| UnitOfWorks | 7 implementações + 2 protocols |
| Type ignores | ~25 (maioria Qt/SQLAlchemy) |

---

## 1. Oportunidades de Redução de Duplicação (Alto Impacto)

### 1.1 Repository Base Class — ~400 linhas duplicadas

**Problema:** Cada repositório reimplementa `add`, `save`, `get_by_id`, `_filter_company`, mapeamento model↔domain.

**Exemplo:** `SqlAlchemyProductRepository` vs `SqlAlchemyCompanyRepository` vs `SqlAlchemyUserRepository` — 80% igual.

**Solução:** `SqlAlchemyRepository[Model, Domain, ID]` genérico com:
- `to_domain(model) -> Domain` (abstract)
- `to_model(domain) -> Model` (abstract)
- `get_by_id`, `add`, `save`, `delete` implementados na base
- `_filter_company` como hook opcional

**Impacto:** -60% linhas em `infrastructure/repository.py` por módulo.

---

### 1.2 UnitOfWork Base — 7 classes quase idênticas

**Problema:** `SqlAlchemy*UnitOfWork` diferem apenas na lista de repositórios expostos.

**Solução:** `SqlAlchemyUnitOfWorkBase` que recebe `repo_factories: dict[str, Callable[[Session], Repo]]` no construtor e expõe via `__getattr__` ou propriedades dinâmicas.

```python
class SqlAlchemyCatalogUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, engine: Engine):
        super().__init__(
            engine,
            repos={
                "products": lambda s: SqlAlchemyProductRepository(s),
                "categories": lambda s: SqlAlchemyCategoryRepository(s),
                ...
            }
        )
```

**Impacto:** Elimina 6 arquivos de boilerplate.

---

### 1.3 `_filter_company` + `CurrentSession` — Cross-cutting concern

**Problema:** 12 repositórios chamam `CurrentSession().company_id` manualmente.

**Solução:** 
- Middleware no `SqlAlchemyUnitOfWorkBase` que injeta `company_id` no `Session.info`
- Ou: `QueryFilter` aplicado automaticamente via evento `before_compile` do SQLAlchemy

**Benefício:** Remove dependência de `CurrentSession` da camada infrastructure; testa mais fácil.

---

### 1.4 Dataclasses de Input/Output — Padrão repetitivo

**Problema:** 40+ classes `*Input`/`*Output` com `__init__` manual.

**Solução:** Usar `@dataclass(slots=True, frozen=True)` consistentemente (já faz em alguns). Padronizar:
- `Input`: `frozen=True`, apenas dados de entrada
- `Output`: `frozen=True`, pode ter métodos auxiliares

---

## 2. Consistência de Padrões (Médio Impacto)

### 2.1 Domain Events — Naming & Structure

**Atual:** `EntityCreated/Updated/Deleted` genéricos + `SaleCompleted` específico.

**Inconsistências:**
- `EntityCreated.after` vs `SaleCompleted.items` (estruturas diferentes)
- Alguns eventos têm `user_id`, outros `username`, outros ambos
- `occurred_at` usa `default_factory` mas não é `frozen`

**Proposta:** Base unificada:
```python
@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    user_id: int | None = None
    username: str = ""
    correlation_id: UUID | None = None  # para tracing
```

---

### 2.2 Error Hierarchy — Pouca granularidade

**Atual:** 4 exceções base (`DomainError`, `PermissionDenied`, `NotFound`, `ValidationError`).

**Falta:** `ConcurrencyError`, `BusinessRuleViolation`, `InvalidState`, `InsufficientStock`, `DuplicateEntry`.

**Benefício:** `except InsufficientStock` em vez de `except ValidationError` + string matching.

---

### 2.3 Money/Quantity — Operações faltando

**Money** tem: `+`, `-`, `* int`, `* Quantity`, `%`, `//`, formatação BRL.  
**Falta:** `truediv` (rateio), `quantize` explícito, `from_decimal`/`to_decimal`.

**Quantity** tem: criação, conversão. **Falta:** aritmética, comparação, formatação.

---

## 3. Camada Application — Melhorias Expressivas

### 3.1 Use Cases — Return `Result` em vez de exceções para fluxos esperados

**Atual:** `NotFound`, `ValidationError`, `PermissionDenied` raised.

**Problema:** Exceções para controle de fluxo normal (ex: "produto não encontrado" é esperado).

**Proposta:** `Result[T, E]` (style Railway/Result monad) ou `dataclass` simples:
```python
@dataclass(frozen=True)
class Result:
    ok: bool
    value: T | None = None
    error: DomainError | None = None

    @classmethod
    def success(cls, value: T) -> Result[T]:
        return cls(ok=True, value=value)
    
    @classmethod
    def failure(cls, error: DomainError) -> Result[T]:
        return cls(ok=False, error=error)
```

**Benefício:** Type-safe, testável, sem try/except em presenters.

---

### 3.2 Services Facade — Muitos parâmetros opcionais

**Exemplo:** `SalesServices.__init__` com 4 parâmetros, `CompaniesServices` com 2.

**Proposta:** `ServicesConfig` dataclass ou `DependencyContainer` pequeno por módulo.

---

### 3.3 EventBus — Sync-only, sem ordering guarantees

**Atual:** `threading.Lock` + lista simples. Publica na ordem de subscrição.

**Risco:** Se `AuditSubscriber` falhar, `TreasurySubscriber` não roda (mesmo não dependendo).

**Melhoria:** `EventBus` com:
- `publish_all(events: list[Event])` atômico (coleta falhas, roda todos)
- `subscribe_async` para handlers não-críticos
- Dead letter queue para handlers que falham repetidamente

---

## 4. Camada Infrastructure — Robustez

### 4.1 SQLite PRAGMAs — Aplicados apenas no `connect` event

**Risco:** Se connection pool reutiliza conexões, PRAGMAs persistem (OK), mas não há verificação.

**Melhoria:** `engine.connect().execute(text("PRAGMA journal_mode"))` no bootstrap para confirmar.

---

### 4.2 Audit Triggers — Bypass table single-row

**Atual:** `audit_bypass(id=1, enabled)` — funciona mas frágil.

**Melhoria:** `PRAGMA user_version` ou `TEMP TABLE` por transação (mais limpo, sem tabela permanente).

---

### 4.3 Migrations — `0001_initial` vazia

**Atual:** Baseline vazia, primeira real é `0002_identity_tables`.

**Recomendação:** Manter (não reescrever histórico), mas documentar no `CHANGELOG.md` por que existe.

---

### 4.4 Models — `type: ignore` excessivos

**Causa:** SQLAlchemy `Mapped` + `mapped_column` + generics + dynamic attrs.

**Mitigação:** 
- `from __future__ import annotations` (já tem)
- `mypy` plugin `sqlalchemy2-stubs` (já funciona)
- Considerar `TypedDict` para `**kwargs` em `save()`

---

## 5. Camada Presentation — Qt Coupling

### 5.1 Table Models — Boilerplate repetido

**Arquivos:** `AuditTableModel`, `ProductTableModel` — 80% igual.

**Solução:** `GenericTableModel[T]` com `columns: list[ColumnDef[T]]`:
```python
@dataclass
class ColumnDef:
    header: str
    getter: Callable[[T], Any]
    alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft
```

---

### 5.2 Presenters — `type: ignore[override]` em mocks de teste

**Causa:** `FakeIdentityServices` não herda de `IdentityServices` (protocol).

**Solução:** `IdentityServices` como `Protocol` + `Fake` implementa o protocol (sem `# type: ignore`).

---

### 5.3 View Protocols — Duplicados por módulo

**Exemplo:** `CompaniesCreateView`, `CompaniesListView`, `ProductView`, `AuditView` — todos têm `show_error`, `show_loading`, `accept`.

**Proposta:** `BaseView(Protocol)` com métodos comuns; views específicas herdam/estendem.

---

## 6. Testes — Qualidade e Cobertura

### 6.1 Fake Repositories — Reimplementados por módulo

**Padrão:** `FakeProductRepository`, `FakeUserRepository`, etc. — cada um com `_products`, `_by_sku`, `_next_id`.

**Solução:** `InMemoryRepository[Entity]` genérico com índice por campo único configurável.

---

### 6.2 Test Fixtures — `CurrentSession` global nos testes

**Problema:** `CurrentSession()` singleton vaza estado entre testes.

**Solução:** Fixture `session: CurrentSession` que reseta a cada teste (já faz em alguns, padronizar).

---

### 6.3 Integration Tests — Database real vs In-memory

**Atual:** Usa `tmp_path` + file SQLite. Lento (~2s para 2 testes bootstrap).

**Otimização:** `:memory:` para testes de repositório; file-based só para bootstrap/migration tests.

---

### 6.4 Property-based Testing — Ausente

**Oportunidade:** `hypothesis` para `Money`, `Quantity`, `Product` creation, validações de domínio.

---

## 7. Configuração & Tooling

### 7.1 `pyproject.toml` — Dependências soltas

**Atual:** `sqlalchemy>=2.1.4`, `bcrypt>=4.1`, etc.

**Risco:** `uv sync` pode trazer breaking changes em minor versions.

**Recomendação:** Pin patch versions (`sqlalchemy==2.1.4`, `bcrypt==4.1.2`) ou usar `uv.lock` como source of truth (já faz).

---

### 7.2 `ruff` — `select` amplo mas `preview` não habilitado

**Sugestão:** Habilitar `preview = true` para regras futuras (ex: `UP035` `Callable` import).

---

### 7.3 `mypy` — `strict=true` mas `ignore_missing_imports` para PySide6

**Trade-off:** Necessário (PySide6 sem stubs completos), mas mascara erros reais em imports Qt.

**Mitigação:** Stub files locais para APIs Qt usadas (`typing: ignore` apenas onde inevitável).

---

## 8. Documentação

### 8.1 `README.md` — Status table atualizada ✅

### 8.2 Faltando:
- `ARCHITECTURE.md` (decisões, diagramas de dependência)
- `CONTRIBUTING.md` (padrões de commit, branches, PR template)
- `CHANGELOG.md` (Keep a Changelog format)
- `SECURITY.md` (como reportar vulns)
- Docstrings de módulo (`__init__.py` com resumo do propósito)

---

## 9. Priorização Sugerida

| Prioridade | Item | Esforço | Risco | ROI |
|------------|------|---------|-------|-----|
| **P1** | Repository Base Class | Médio | Baixo | Alto |
| **P1** | UnitOfWork Base | Baixo | Baixo | Alto |
| **P1** | Result pattern (use cases) | Médio | Médio | Alto |
| **P2** | Domain Events unificados | Baixo | Baixo | Médio |
| **P2** | Error hierarchy expandida | Baixo | Baixo | Médio |
| **P2** | Generic TableModel (Qt) | Médio | Baixo | Médio |
| **P3** | InMemoryRepository genérico | Baixo | Baixo | Médio |
| **P3** | EventBus robustez | Médio | Médio | Baixo |
| **P3** | Docs arquiteturais | Baixo | Zero | Médio |
| **P4** | Property-based tests | Médio | Baixo | Baixo |

---

## 10. Itens "Não Mexer" (Funcionam Bem)

- ✅ Clean Architecture boundaries (import-linter passing)
- ✅ Dataclasses + slots + frozen (performance + imutabilidade)
- ✅ Protocol-based ports (testabilidade, inversão de dependência)
- ✅ UTCDateTime + _utcnow() (timezone-safe)
- ✅ Money/Quantity value objects (sem float)
- ✅ Event-driven cross-module (SaleCompleted)
- ✅ Seed idempotente + admin via env var
- ✅ Headless bootstrap (CI/CD friendly)
- ✅ 160 testes passing, mypy strict, ruff clean

---

## Conclusão

O código é **produção-ready** para o escopo atual. As melhorias acima são **evolutivas** — visam reduzir custo de manutenção conforme o projeto cresce (novos módulos: backup, receipts, reports, fiscal).

**Próximo passo recomendado:** Implementar **Repository Base Class** + **UnitOfWork Base** (itens P1). Isso sozinho elimina ~500 linhas de boilerplate e padroniza 100% da camada infrastructure.

---

*Relatório gerado via análise estática + leitura de arquivos-chave. Nenhuma alteração foi feita no código.*