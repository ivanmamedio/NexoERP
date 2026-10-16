# Como conduzir o Qwen no desenvolvimento

Modelos de código funcionam melhor com **contexto fixo + tarefas pequenas + critério de pronto verificável**. Pedir "faça o ERP inteiro" gera código inconsistente. O fluxo é:

1. Salve o contexto do projeto num arquivo (`QWEN.md` na raiz, se usar o Qwen Code CLI, que o lê automaticamente; senão cole o texto no início de cada conversa).
2. Passe **uma tarefa por vez**, na ordem abaixo.
3. Após cada tarefa: rode `pytest`, `ruff` e `mypy`, faça commit e só então avance.
4. Se o Qwen se perder, cole o erro completo e peça correção. Não reexplique o projeto.

---

## Passo 1: Contexto fixo (salve como `QWEN.md`)

````markdown
# PAPEL
Você é um engenheiro de software sênior em Python. Você implementa, passo a passo,
um ERP desktop open-source para pequenos comércios, seguindo estritamente este documento.

# PROJETO
ERP desktop offline-first, multiplataforma (Windows 10+ e Linux), leve e gratuito.
Módulos: multi-empresa, usuários com RBAC, produtos/estoque, precificação, caixa
(abertura, sangria, suprimento, fechamento), PDV com cupom NÃO FISCAL 58/80mm,
tesouraria (contas a pagar/receber, fluxo de caixa), auditoria, backup, relatórios.
Sem integração fiscal (existe apenas uma interface vazia FiscalPort).

# STACK (não troque, não adicione dependências sem me avisar)
Python 3.12, PySide6 (Qt Widgets, sem QML), SQLite (WAL, foreign_keys=ON),
SQLAlchemy 2.0 (estilo tipado, Mapped[]), Alembic, bcrypt, python-escpos,
platformdirs, pytest, pytest-qt, ruff, mypy (strict), import-linter, uv.

# ARQUITETURA
Monolito modular + Clean Architecture. Estrutura:
src/erp/{config, shared/{domain,application,infrastructure,ui}, modules/<modulo>/{domain,application,infrastructure,presentation}, app}
Módulos: identity, companies, catalog, pricing, cash, sales, treasury, receipts, audit, backup, reports, fiscal.

Regras de dependência (INVIOLÁVEIS):
- domain não importa nada de fora do próprio domain e do shared/domain.
- application depende só de domain e define as interfaces (ports) dos repositórios.
- infrastructure implementa os ports (SQLAlchemy, ESC/POS, filesystem).
- presentation (Qt) só chama casos de uso via presenters; nenhuma regra de negócio em widgets.
- Um módulo só importa outro via application/ público dele, nunca infrastructure.
- Composition root em bootstrap.py faz toda a injeção de dependências.

# CONVENÇÕES
- Dinheiro SEMPRE em centavos (int) via value object Money. Nunca float.
- Quantidade fracionada em milésimos (int).
- Cada caso de uso roda em UMA transação (UnitOfWork). Venda + estoque + caixa + financeiro + auditoria são atômicos.
- Comunicação entre módulos por EventBus síncrono em memória (ex.: SaleCompleted).
- Multi-empresa: company_id em toda tabela de negócio; empresa ativa vem de CurrentSession.
- Permissões são verificadas NO CASO DE USO, nunca apenas escondendo botões.
- Vendas são imutáveis: correção é cancelamento/estorno com permissão + auditoria.
- Estoque é livro de movimentos (stock_movements); products.stock_qty é cache.
- Auditoria via eventos de domínio, com before/after em JSON e hash encadeado.
- Banco fora da pasta de instalação (platformdirs). Backup usa sqlite3.Connection.backup(), nunca cópia direta.
- Textos de UI em português do Brasil; código, nomes e comentários técnicos em inglês.
- Type hints completos, docstrings curtas, funções pequenas, sem código morto.
- Todo caso de uso novo vem com teste unitário. Todo repositório novo vem com teste de integração (SQLite em memória).

# FORMA DE TRABALHAR
- Faça SOMENTE a tarefa pedida. Não antecipe fases futuras.
- Antes de codar, liste em 3 a 6 linhas os arquivos que vai criar/alterar.
- Entregue o código completo de cada arquivo (sem "..." nem trechos omitidos), indicando o caminho.
- Ao final, informe: comandos para rodar os testes e o que ficou pendente.
- Se algo estiver ambíguo, escolha a opção mais simples, declare a suposição em uma linha e siga.
- Nunca invente APIs de bibliotecas. Se não tiver certeza, diga e use a alternativa mais segura.
````

---

## Passo 2: Prompts por tarefa (cole um de cada vez)

### Fase 0: Fundação

**Tarefa 0.1: Esqueleto do repositório**
```
Tarefa 0.1: Crie o esqueleto do repositório conforme a estrutura do QWEN.md.
Entregue: pyproject.toml (uv, dependências, config de ruff/mypy strict/pytest),
.gitignore, README.md básico, LICENSE (AGPL-3.0), .importlinter com contratos
que impõem as regras de dependência, pastas vazias com __init__.py,
src/erp/__main__.py que abre uma QMainWindow vazia com título "ERP".
Pronto quando: `uv run python -m erp` abre a janela e `uv run pytest` roda (mesmo sem testes).
```

**Tarefa 0.2: Núcleo compartilhado**
```
Tarefa 0.2: Implemente em shared/:
- domain: Money (centavos, soma/subtração/multiplicação por quantidade e percentual com arredondamento
  half-even, formatação "R$ 1.234,56"), Quantity, Entity base, erros de domínio (DomainError,
  PermissionDenied, NotFound, ValidationError).
- application: UnitOfWork (interface), EventBus síncrono (subscribe/publish tipado), CurrentSession.
- infrastructure: engine SQLite com PRAGMA journal_mode=WAL, foreign_keys=ON, busy_timeout;
  Base declarativa com created_at/updated_at; SqlAlchemyUnitOfWork.
- config: paths via platformdirs, logging com arquivo rotativo.
Testes unitários completos para Money (incluindo arredondamento e casos de borda) e EventBus.
```

**Tarefa 0.3: Alembic e bootstrap**
```
Tarefa 0.3: Configure o Alembic para rodar programaticamente na inicialização do app
(função run_migrations() chamada no bootstrap, antes de abrir a UI). Crie bootstrap.py como composition root.
Crie a primeira migração vazia e um teste de integração que cria o banco do zero e verifica as PRAGMAs.
```

**Tarefa 0.4: Empacotamento inicial no CI**
```
Tarefa 0.4: Crie packaging/pyinstaller.spec (modo onedir), packaging/windows/installer.iss (Inno Setup),
packaging/linux (AppImage + nfpm.yaml para .deb + .desktop) e os workflows
.github/workflows/ci.yml (ruff, mypy, import-linter, pytest em windows-latest e ubuntu-22.04)
e release.yml (dispara em tag v*, gera .exe, AppImage e .deb e publica no GitHub Releases).
Explique como testar localmente o build do PyInstaller.
```

### Fase 1: Identidade, Empresas e Catálogo

**Tarefa 1.1: Identity (domínio e persistência)**
```
Tarefa 1.1: Módulo identity. Domain: User, Role, Permission (código tipo "product.price.update"),
política de senha e de bloqueio após 5 tentativas. Application: ports (UserRepository, PasswordHasher),
casos de uso: CreateUser, Authenticate, ChangePassword, AssignRole, CheckPermission.
Infrastructure: modelos SQLAlchemy (users, roles, permissions, role_permissions, user_company_roles),
repositórios, BcryptHasher. Migração Alembic. Seed dos papéis Administrador, Gerente, Caixa e Financeiro
com as permissões do QWEN.md e usuário admin inicial com must_change_password=True.
Testes: o Caixa NÃO tem product.price.update nem treasury.view.
```

**Tarefa 1.2: Identity (telas)**
```
Tarefa 1.2: Telas de login, troca obrigatória de senha, e gestão de usuários/papéis (PySide6).
Use o padrão View + Presenter. A MainWindow só mostra os menus que o usuário pode acessar,
mas a verificação real continua nos casos de uso. Implemente timeout de sessão ociosa configurável.
Teste os presenters sem abrir janela e um teste pytest-qt do login.
```

**Tarefa 1.3: Companies**
```
Tarefa 1.3: Módulo companies: CRUD de estabelecimentos, seleção da empresa ativa após o login,
troca de empresa pela barra de status, e o filtro automático por company_id nos repositórios
(via CurrentSession). Teste: dados da empresa A nunca aparecem na sessão da empresa B.
```

**Tarefa 1.4: Audit (antes do catálogo)**
```
Tarefa 1.4: Módulo audit: tabela audit_logs com hash encadeado (prev_hash/hash), triggers SQLite que
bloqueiam UPDATE e DELETE, subscriber do EventBus que grava eventos de auditoria com before/after,
função verify_chain() que detecta adulteração, e tela de consulta com filtros (usuário, data, ação).
Teste: alterar manualmente um registro faz verify_chain() falhar.
```

**Tarefa 1.5: Catalog**
```
Tarefa 1.5: Módulo catalog: Category (hierárquica), Supplier, Product (sku, múltiplos códigos de barras
únicos por empresa, unidade, custo, margem, preço, estoque mínimo, vendido por peso), stock_movements
como livro de movimentos com cache em stock_qty, price_history. Casos de uso: CreateProduct, UpdateProduct,
UpdatePrice (exige permissão product.price.update e emite evento de auditoria), AdjustStock,
ListLowStock. Telas de cadastro com busca rápida e alerta de estoque mínimo.
Testes: Caixa não altera preço; ajuste de estoque gera movimento; preço alterado gera price_history e auditoria.
```

**Tarefa 1.6: Pricing**
```
Tarefa 1.6: Módulo pricing: serviço de domínio puro que calcula
preço = (custo + custos_fixos) / (1 - (imposto% + taxa_cartão% + margem%)), com modo "taxa média ponderada"
e modo "pior caso". Valide denominador <= 0 com erro claro. Retorne também a margem líquida real.
Tela de assistente com resultado em tempo real e botão "aplicar ao produto" (respeitando permissão).
Teste: custo 10,00 / imposto 6% / cartão 3% / margem 30% = R$ 16,39.
```

### Fase 2: Caixa e PDV

**Tarefa 2.1: Cash**
```
Tarefa 2.1: Módulo cash: cash_registers, cash_sessions, cash_movements. Casos de uso: OpenCashSession,
RegisterSangria, RegisterSuprimento, CloseCashSession. Regras: uma sessão aberta por terminal;
esperado_dinheiro = abertura + vendas em dinheiro + suprimentos - sangrias; Pix e cartão conferidos
contra o total vendido; fechamento cego opcional; diferença calculada e auditada.
Sangria exige permissão cash.sangria. Relatório de fechamento do turno (dados estruturados, sem UI ainda).
Testes cobrindo todos os cenários de conferência, inclusive sobra e falta.
```

**Tarefa 2.2: Sales (domínio e casos de uso)**
```
Tarefa 2.2: Módulo sales: Sale, SaleItem (com snapshot de descrição e preço), SalePayment (pagamentos mistos e troco).
Casos de uso: StartSale, AddItem (por código de barras/SKU/nome), ApplyDiscount (permissão sale.discount OU
autorização de supervisor por PIN, registrando os dois usuários na auditoria), FinalizeSale, CancelSale/CancelItem
(estorno de estoque e caixa, permissão sale.cancel). FinalizeSale publica SaleCompleted; os módulos catalog, cash,
treasury e audit reagem via EventBus, dentro da mesma transação.
Testes: venda atômica (falha no estoque desfaz tudo), troco, pagamento misto, estorno.
```

**Tarefa 2.3: Tela do PDV**
```
Tarefa 2.3: Tela do PDV 100% operável por teclado: campo de leitura sempre focado (leitor de código de barras
envia Enter), multiplicador "3*código", F-keys (F2 pagamento, F4 desconto, F6 cancelar item, F8 cancelar venda,
Esc voltar), tabela de itens, total grande, diálogo de pagamento misto, diálogo de PIN do supervisor.
Presenter testado sem UI. Desempenho: busca por nome com debounce e índice no banco.
```

**Tarefa 2.4: Receipts**
```
Tarefa 2.4: Módulo receipts: gerador de cupom em formato neutro (linhas/colunas conforme largura 32/48 caracteres
para 58/80mm), cabeçalho/rodapé por empresa, e a linha em destaque "NAO E DOCUMENTO FISCAL".
Adapters: preview em tela (QTextEdit monoespaçado), ESC/POS via python-escpos (USB/rede), Windows via spooler RAW (win32print,
import condicional) e Linux via CUPS. Comando de abertura de gaveta. Configuração de impressora nas settings.
Teste do gerador com snapshots de texto para 58mm e 80mm.
```

### Fase 3: Tesouraria

```
Tarefa 3.1: Módulo treasury: financial_categories, payables, receivables, financial_entries (livro-razão).
Casos de uso: CreatePayable (com parcelamento e recorrência), PayPayable, CreateReceivable, ReceiveReceivable.
Subscribers: SaleCompleted e movimentos de caixa geram financial_entries automaticamente.
Todo acesso exige permissão treasury.*; teste que Caixa é bloqueado no caso de uso.

Tarefa 3.2: Fluxo de caixa diário/mensal, controle de despesas por categoria e alertas de vencimento
(contas a vencer em N dias). Telas com filtros por período.
Teste de reconciliação: total do fluxo = vendas + recebimentos - pagamentos - sangrias no período.
```

### Fase 4: Relatórios e Backup

```
Tarefa 4.1: Módulo backup: BackupService usando sqlite3.Connection.backup(), PRAGMA integrity_check,
zip com checksum SHA-256, rotação (30 diários + 12 mensais), destino secundário configurável,
gatilhos (fechamento de caixa, primeiro uso do dia, fechamento do app) e backup automático antes de qualquer migração.
Tela de restauração guiada que salva cópia do banco atual antes de sobrescrever.
Teste: backup, corromper, restaurar e comparar os dados.

Tarefa 4.2: Módulo reports: vendas por período/produto/operador, estoque baixo, margem, DRE simples,
fechamento de caixa. Exportação CSV e PDF. Consultas agregadas direto em SQL (sem carregar entidades).
Imports pesados (PDF) feitos de forma lazy.
```

### Fase 5: Endurecimento

```
Tarefa 5.1: Script de carga que gera 50 mil produtos e 100 mil vendas; meça abertura do app, busca no PDV e
fechamento de caixa. Aponte gargalos e crie os índices necessários via migração.

Tarefa 5.2: Tratamento global de exceções (log + mensagem amigável + opção de copiar o relatório de erro),
revisão de segurança (nenhuma regra de permissão só na UI, senhas nunca em log), teste de migração
da versão N-1 para N com dados reais, e documentação do usuário em docs/ (instalação em 5 minutos, primeiro uso, backup).
```

---

## Passo 3: Prompts de apoio (use quando precisar)

**Revisão após cada tarefa**
```
Revise o código que você acabou de gerar contra o QWEN.md. Liste violações das regras de dependência,
uso de float em dinheiro, regras de negócio na UI, permissões não verificadas no caso de uso,
falta de transação e falta de testes. Corrija cada item apontado e mostre apenas os arquivos alterados.
```

**Quando ocorrer erro**
```
Ao rodar `<comando>` apareceu este erro:
<cole o traceback completo>
Explique a causa em 2 linhas e corrija mostrando só os arquivos alterados. Não mude a arquitetura.
```

**Quando o Qwen "esquecer" o contexto**
```
Releia o QWEN.md. Seu último código violou: <regra>. Refaça a tarefa respeitando essa regra.
```

---

## Dicas práticas para usar bem o Qwen

- **Modelo:** prefira um Qwen focado em código (família Qwen-Coder, a maior que seu hardware ou sua API suportar). Modelos pequenos erram mais em SQLAlchemy 2.0 e Qt.
- **Contexto longo:** em conversas muito longas o modelo degrada. Inicie um chat novo a cada tarefa e cole apenas o `QWEN.md`, mais os arquivos relevantes já gerados (por exemplo, os ports do módulo que vai ser consumido).
- **Versionamento:** commit por tarefa (`feat(catalog): ...`). Se o Qwen quebrar algo, você reverte sem perder o resto.
- **Valide o que ele afirma:** modelos às vezes inventam métodos de biblioteca. Rodar `mypy` e os testes é a rede de segurança; não confie só no "pronto".
- **Revise você mesmo os pontos críticos:** Money, UnitOfWork, auditoria, fechamento de caixa e backup. São onde um bug custa dinheiro real ao lojista.
- **Ordem importa:** não pule a Tarefa 1.4 (auditoria) para depois do catálogo, pois adaptar auditoria depois é bem mais caro.

Se quiser, posso empacotar tudo isso (contexto + prompts) em um único arquivo `.md` pronto para colocar no repositório, ou escrever agora o prompt detalhado de alguma tarefa específica, como o fechamento de caixa.