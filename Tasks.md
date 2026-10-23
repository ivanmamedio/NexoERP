# Como conduzir a IA no desenvolvimento do NexoERP

Modelos de código funcionam melhor com **contexto fixo + tarefas pequenas + critério de pronto verificável**. Pedir "faça o ERP inteiro" gera código inconsistente. O fluxo é:

1. Salve o contexto do projeto num arquivo na raiz (`CONTEXTO.md`). Se a sua ferramenta lê automaticamente um arquivo com nome específico (por exemplo `AGENTS.md` ou `CLAUDE.md`), use o nome que ela espera; senão, cole o texto no início de cada conversa.
2. Passe **uma tarefa por vez**, na ordem abaixo, **cada uma em um chat novo**.
3. Ao final de cada tarefa, rode o **critério de pronto** (seção abaixo), confira o `git status` e **você** faz o commit. A IA nunca faz commit.
4. Se a IA se perder, cole o erro completo e peça a correção. Não reexplique o projeto.

---

## Status atual

Baseado na auditoria de 18/10/2026 e na varredura de arquivos vazios, atualizado em 20/10/2026 com o diagnóstico da tela de login e do build no Fedora. **Atualizado em 23/10/2026 após correções da Fase C e auditoria completa.** Confirme cada item rodando o critério de pronto antes de marcá-lo como concluído de verdade.

| Tarefa | Status |
|---|---|
| 0.1 a 0.3 Fundação, núcleo, Alembic/bootstrap | ✅ Implementadas. Bootstrap corrigido (migração 0009 com bypass de auditoria) |
| 0.4 Empacotamento no CI | ✅ Configurado. Build PyInstaller onedir validado localmente (logo incluído). Build real em VM Windows/Linux **pendente** |
| 1.1 a 1.6 Identity, Companies, Audit, Catalog, Pricing | ✅ Implementadas (domínio, aplicação, infraestrutura, apresentação) |
| 1.2 Identity (telas) | ✅ Corrigidos: logo carrega no build, sem FramelessWindowHint/WA_TranslucentBackground, sem artefato duplicado. `admin/admin` não existe (seed exige NEXOERP_ADMIN_PASSWORD, migração 0009 força troca) |
| 1.7 Configurações (NOVA) | ✅ Implementada (`settings` module: company_id, receipt header/footer, session timeout, printer settings) |
| 2.1 Cash (domínio, casos de uso) | ✅ Implementada |
| 2.2.1 Telas do Caixa (NOVA) | ✅ Implementada (`cash/presentation`: abertura, sangria, suprimento, fechamento, relatório) |
| 2.2 Sales (domínio, casos de uso) | ✅ Implementada (atômica, pagamentos mistos, desconto com PIN, cancelamento/estorno) |
| 2.3 Tela PDV (NOVA) | ✅ Implementada (`pos_view.py`, `pos_presenter.py`: teclado, multiplicador `3*código`, pagamento misto, desconto supervisor) |
| 2.4 Receipts (NOVA) | ✅ Implementada (gerador, preview, ESC/POS, Windows spooler, CUPS, settings dialog) — mypy zerado |
| 2.5 Compras/Inventário (NOVA) | ✅ Implementada (`purchases` module: RegisterPurchase, CountInventory) |
| 3.1 Treasury | ✅ Implementada (domínio, app, infra: payables, receivables, financial_entries, subscribers) |
| 3.2 Fluxo de Caixa UI (NOVA) | ⚠️ Parcial (`treasury/presentation` só tem `cash_flow_presenter.py` básico) |
| 3.3 Clientes/Fiado (NOVA, opcional) | ✅ Implementada (`customers` module) |
| 4.1 Backup | ✅ Implementada (sqlite3.backup, rotação, checksum, triggers, restore guiado) |
| 4.2 Reports | ✅ Implementada (vendas/estoque/margem/DRE/fechamento, CSV/PDF, SQL direto) |
| 4.3 FiscalPort | ✅ Implementada (apenas Protocol, sem emissão real) |
| 4.4 Import CSV (NOVA) | ✅ Implementada (`import_csv` module: preview, validação, transação única, auditoria) |
| 5.x Endurecimento | ❌ Não iniciado |

**Fase C (C.1 a C.8): ✅ CONCLUÍDA** — Todos os itens resolvidos ou verificados como não aplicáveis/inexistentes.

**Próxima prioridade real:** Completar `treasury/presentation` (Tarefa 3.2) → Tarefa 5.x (Endurecimento: carga 50k/100k, exceções, build real em VM, docs usuário).

---

## Passo 1: Contexto fixo (salve como `CONTEXTO.md`)

````markdown
# PAPEL
Você é um engenheiro de software sênior em Python. Você implementa, passo a passo,
um ERP desktop open-source para pequenos comércios, seguindo estritamente este documento.
Responda sempre em português do Brasil.

# PROJETO
ERP desktop offline-first, multiplataforma (Windows 10+ e Linux), leve e gratuito.
Módulos: multi-empresa, usuários com RBAC, produtos/estoque, precificação, caixa
(abertura, sangria, suprimento, fechamento), PDV com cupom NÃO FISCAL 58/80mm,
tesouraria (contas a pagar/receber, fluxo de caixa), auditoria, backup, relatórios.
Sem integração fiscal (existirá apenas uma interface FiscalPort, criada na tarefa 4.3).
Windows 7 está fora de escopo. Não migrar para Qt 5, PyQt5 nem Python mais antigo.

# STACK (não troque, não adicione dependências sem me avisar)
Python 3.12, PySide6 (Qt Widgets, sem QML), SQLite (WAL, foreign_keys=ON),
SQLAlchemy 2.0 (estilo tipado, Mapped[]), Alembic, bcrypt, platformdirs, pytest, pytest-qt,
ruff, mypy (strict), import-linter, uv. python-escpos entra somente na tarefa 2.4.

# ARQUITETURA
Monolito modular + Clean Architecture. Estrutura:
src/erp/{config, shared/{domain,application,infrastructure,ui}, modules/<modulo>/{domain,application,infrastructure,presentation}}
Módulos existentes: identity, companies, catalog, pricing, cash, sales, treasury, audit.
Módulos planejados (receipts, backup, reports, fiscal): criar a pasta SOMENTE na tarefa correspondente.
Não crie pastas, camadas ou arquivos vazios "para o futuro". Só crie a camada que tem código real.

Regras de dependência (INVIOLÁVEIS):
- domain não importa nada de fora do próprio domain e do shared/domain.
- application depende só de domain e define as interfaces (ports) dos repositórios.
- infrastructure implementa os ports (SQLAlchemy, ESC/POS, filesystem).
- presentation (Qt) só chama casos de uso via presenters; nenhuma regra de negócio em widgets.
- Um módulo só importa outro módulo via o application/ público dele (ports e casos de uso).
  Nunca importa domain, infrastructure ou presentation de outro módulo.
- Se um módulo precisa de algo de outro, prefira definir um port próprio em application/ports.py
  e ligar o adaptador no bootstrap.py. Preocupações transversais (checagem de permissão, sessão,
  UnitOfWork) ficam em shared/application.
- Composition root em bootstrap.py faz toda a injeção de dependências.
- O .importlinter deve impor exatamente estas regras e ser atualizado a cada módulo novo.
  Ao alterá-lo, prove que uma violação inserida de propósito faz o lint falhar.

# CONVENÇÕES
- Dinheiro SEMPRE em centavos (int) via value object Money. Nunca float.
- Quantidade fracionada em milésimos (int).
- Datas e horas: sempre UTC com timezone (aware), com UM único padrão em todo o projeto
  (tipo UTCDateTime). Nunca misturar server_default=func.now() com defaults em Python.
- Cada caso de uso roda em UMA transação (UnitOfWork). Venda + estoque + caixa + financeiro + auditoria são atômicos.
- Comunicação entre módulos por EventBus síncrono em memória (ex.: SaleCompleted).
- Multi-empresa: company_id em toda tabela de negócio; empresa ativa vem de CurrentSession.
  Todo repositório novo vem com teste de duas empresas provando que uma nunca vê dados da outra.
- Permissões são verificadas NO CASO DE USO, nunca apenas escondendo botões.
- Vendas são imutáveis: correção é cancelamento/estorno com permissão + auditoria.
- Estoque é livro de movimentos (stock_movements); products.stock_qty é cache.
- Auditoria via eventos de domínio, com before/after em JSON e hash encadeado.
- Banco fora da pasta de instalação (platformdirs). Backup usa sqlite3.Connection.backup(), nunca cópia direta.
- Migrações Alembic: nunca editar migração já aplicada; toda mudança de schema é uma migração nova
  (SQLite em modo batch). A 0001 vazia é baseline intencional e deve ser mantida.
- SQLite via SQLAlchemy: UMA statement por execute(). Não usar executescript() dentro de transação
  (faz COMMIT implícito) e não dividir DDL por ";" (CREATE TRIGGER tem ";" internos).
- Segurança: não existe senha padrão. O primeiro administrador usa credencial explícita
  (variável NEXOERP_ADMIN_PASSWORD ou tela de primeiro uso) com must_change_password=True.
  Nunca registrar senha ou hash em log.
- Textos de UI em português do Brasil; código, nomes e comentários técnicos em inglês.
- Type hints completos, docstrings curtas, funções pequenas, sem código morto.
- Placeholder não é funcionalidade concluída: não marcar como pronto.
- Todo caso de uso novo vem com teste unitário. Todo repositório novo vem com teste de integração
  (SQLite temporário e isolado; nunca dados reais nem o banco de produção).
- O README (tabela de status e comandos) é atualizado ao fim de cada tarefa, dizendo só o que está
  implementado e testado.

# UI (Qt)
- Janelas normais do sistema (com borda). Proibido Qt.FramelessWindowHint e WA_TranslucentBackground:
  são instáveis no Wayland e causam artefatos (quadrado branco). Se for realmente necessário, pergunte antes.
- Proibido QGraphicsEffect (sombra, blur) em widget que contém filhos. Sombra só em um QFrame vazio
  posicionado atrás do card.
- Estilo em QSS por objectName, definido em um único lugar. Nada de setStyleSheet repetido em cada widget.
- Recursos (imagens, ícones): sempre via shared/ui/resources.py (resource_path), que funciona em dev e no
  PyInstaller (sys._MEIPASS). Todo recurso novo entra em datas do pyinstaller.spec na mesma tarefa.
- Testar no Linux em Wayland e em X11 (QT_QPA_PLATFORM=wayland e =xcb). Em testes automáticos, usar offscreen.

# CRITÉRIO DE PRONTO (toda tarefa)
Rodar e mostrar as saídas REAIS, separando passou / falhou / não executado:
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run import-linter lint
git status --short
Nunca declarar suíte verde se algo falhou ou não rodou. Nunca remover teste que falha, relaxar mypy/ruff
ou suprimir warning para obter verde: corrigir a causa.

# GIT
Nunca fazer commit, push, git reset --hard, git clean nem qualquer comando destrutivo.
Preservar alterações não commitadas do usuário. Quem faz o commit é o usuário, um por tarefa.

# FORMA DE TRABALHAR
- Faça SOMENTE a tarefa pedida. Não antecipe fases futuras.
- Antes de codar, liste em 3 a 6 linhas os arquivos que vai criar/alterar/remover.
- Entregue o código completo de cada arquivo (sem "..." nem trechos omitidos), indicando o caminho.
- Entregue cada arquivo UMA vez. Se notar blocos repetidos ou o arquivo ficando enorme, pare, descarte e reescreva curto.
- Ao final, informe: comandos para rodar os testes, resultado real do critério de pronto e o que ficou pendente.
- Se algo estiver ambíguo, escolha a opção mais simples, declare a suposição em uma linha e siga.
  Se a decisão for arquitetural, destrutiva (dados, migração, remoção) ou mudar SO suportado, PARE e pergunte.
- Nunca invente APIs de bibliotecas. Se não tiver certeza, diga e use a alternativa mais segura.
````

---

## Passo 2: Prompts por tarefa (cole um de cada vez, em chat novo, junto com o `CONTEXTO.md`)

### Fase 0: Fundação

**Tarefa 0.1: Esqueleto do repositório**
```
Tarefa 0.1: Crie o esqueleto do repositório conforme a estrutura do CONTEXTO.md.
Entregue: pyproject.toml (uv, dependências, config de ruff/mypy strict/pytest),
.gitignore, README.md básico (instalação e execução para Windows PowerShell e Linux, usando `uv run`),
LICENSE (AGPL-3.0), .importlinter com contratos que impõem as regras de dependência,
src/erp/__main__.py que abre uma QMainWindow vazia com título "ERP".
Crie apenas as pastas necessárias para o que existe agora; sem módulos vazios de fases futuras.
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
  Base declarativa; tipo UTCDateTime e UM padrão único para created_at/updated_at; SqlAlchemyUnitOfWork.
- config: paths via platformdirs, logging com arquivo rotativo.
Testes unitários completos para Money (incluindo arredondamento e casos de borda) e EventBus.
```

**Tarefa 0.3: Alembic e bootstrap**
```
Tarefa 0.3: Configure o Alembic para rodar programaticamente na inicialização do app
(função run_migrations() chamada no bootstrap, antes de abrir a UI). Crie bootstrap.py como composition root.
Crie a primeira migração vazia (baseline) e um teste de integração que cria o banco do zero,
verifica as PRAGMAs e confirma que rodar o bootstrap duas vezes é idempotente.
```

**Tarefa 0.4: Empacotamento inicial no CI**
```
Tarefa 0.4: Crie packaging/pyinstaller.spec (modo onedir, incluindo scripts de migração e plugins Qt),
packaging/windows/installer.iss (Inno Setup), packaging/linux (AppImage + nfpm.yaml para .deb + .desktop)
e os workflows .github/workflows/ci.yml (ruff check, ruff format --check, mypy, import-linter, pytest em
windows-latest e ubuntu-22.04) e release.yml (dispara em tag v*, gera .exe, AppImage e .deb e publica no GitHub Releases).
Explique como testar localmente o build do PyInstaller.
```

### Fase 1: Identidade, Empresas e Catálogo

**Tarefa 1.1: Identity (domínio e persistência)**
```
Tarefa 1.1: Módulo identity. Domain: User, Role, Permission (código tipo "product.price.update"),
política de senha e de bloqueio após 5 tentativas. Application: ports (UserRepository, PasswordHasher),
casos de uso: CreateUser, Authenticate, ChangePassword, AssignRole, CheckPermission.
Infrastructure: modelos SQLAlchemy (users, roles, permissions, role_permissions, user_company_roles),
repositórios, BcryptHasher. Migração Alembic. Seed idempotente dos papéis Administrador, Gerente, Caixa e Financeiro
com as permissões do CONTEXTO.md. O primeiro administrador é criado com credencial explícita (sem senha padrão)
e must_change_password=True.
Testes: o Caixa NÃO tem product.price.update nem treasury.view; lockout expira corretamente (UTC aware).
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
Cada DDL é executado em chamadas execute() separadas. Teste: alterar manualmente um registro faz
verify_chain() falhar; o bootstrap em banco vazio e repetido é idempotente.
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
Tela de assistente com resultado em tempo real e botão "aplicar ao produto" (respeitando permissão,
via application/ público do catalog, sem importar domain nem infrastructure dele).
Teste: custo 10,00 / imposto 6% / cartão 3% / margem 30% = R$ 16,39.
```

**Tarefa 1.7: Configurações** *(nova: a 1.2 fala em timeout configurável e a 2.4 em impressora "nas settings", mas nenhuma tarefa criava essa tela)*
```
Tarefa 1.7: Configurações por empresa. Tabela settings (company_id, chave, valor tipado), casos de uso GetSetting e
UpdateSetting com permissão settings.update e auditoria do before/after. Tela de Configurações (View + Presenter) com:
dados da empresa para o cabeçalho/rodapé do cupom (nome, CNPJ opcional, endereço, mensagem) e timeout de sessão ociosa.
A seção de impressora entra na 2.4; não crie campos ou placeholders dela agora. Seed da permissão settings.update para
Administrador e Gerente. Crie pasta de módulo nova somente se houver código real nela.
Testes: duas empresas com valores diferentes; Caixa bloqueado no caso de uso; alteração gera auditoria.
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
O sales acessa o catalog SOMENTE por ports (definidos no próprio sales ou no application/ público do catalog),
com adaptadores ligados no bootstrap. Nunca importa catalog.infrastructure nem catalog.domain.
Testes: venda atômica (falha no estoque desfaz tudo), troco, pagamento misto, estorno, permissão negada.
```

**Tarefa 2.2.1: Telas do Caixa** *(nova: a 2.1 não tinha UI e a 2.3 só cobre o PDV)*
```
Tarefa 2.2.1: Telas do módulo cash (PySide6, View + Presenter): abertura de caixa, sangria, suprimento,
fechamento (com modo cego opcional) e exibição do relatório de fechamento. As telas só chamam casos de uso
via presenters; as permissões continuam verificadas nos casos de uso. Crie cash/presentation SOMENTE agora.
Testes dos presenters sem abrir janela e um teste pytest-qt de abertura e fechamento de caixa.
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
Tarefa 2.4: Crie o módulo receipts (pasta nova): gerador de cupom em formato neutro (linhas/colunas conforme largura 32/48 caracteres
para 58/80mm), cabeçalho/rodapé por empresa, e a linha em destaque "NAO E DOCUMENTO FISCAL".
Adapters: preview em tela (QTextEdit monoespaçado), ESC/POS via python-escpos (USB/rede), Windows via spooler RAW (win32print,
import condicional) e Linux via CUPS. Comando de abertura de gaveta. Configuração de impressora nas settings.
Autorizado a adicionar python-escpos ao projeto. Atualize o .importlinter.
Teste do gerador com snapshots de texto para 58mm e 80mm.
```

**Tarefa 2.5: Compras e inventário** *(nova: o catálogo tem Supplier e AdjustStock, mas não existe entrada de mercadoria nem contagem de estoque)*
```
Tarefa 2.5: Entrada de mercadoria e inventário. Casos de uso: RegisterPurchase (fornecedor, itens, quantidade, custo, data;
gera stock_movements de entrada, atualiza o custo do produto exigindo permissão catalog.cost.update e emite evento de auditoria)
e CountInventory (contagem física; a diferença vira movimento de ajuste com motivo obrigatório). O acesso ao catalog é só por
ports/application público. A geração de conta a pagar a partir da compra fica para a 3.1; não antecipe.
Telas de entrada de mercadoria e de contagem. Testes: entrada aumenta estoque e atualiza custo; contagem gera movimento;
Caixa bloqueado; duas empresas.
```

### Fase 3: Tesouraria

```
Tarefa 3.1: Módulo treasury: financial_categories, payables, receivables, financial_entries (livro-razão).
Casos de uso: CreatePayable (com parcelamento e recorrência), PayPayable, CreateReceivable, ReceiveReceivable.
Subscribers: SaleCompleted e movimentos de caixa geram financial_entries automaticamente.
Todo acesso exige permissão treasury.*; teste que Caixa é bloqueado no caso de uso.
Se parte já existe (financial_entries e subscribers), implemente apenas o que falta.

Tarefa 3.2: Fluxo de caixa diário/mensal, controle de despesas por categoria e alertas de vencimento
(contas a vencer em N dias). Telas com filtros por período (cria treasury/presentation somente agora).
Teste de reconciliação: total do fluxo = vendas + recebimentos - pagamentos - sangrias no período.
```

**Tarefa 3.3: Clientes e venda a prazo (fiado)** *(nova e opcional; a 3.1 tem contas a receber, mas sem cliente não há quem deva. Faça só depois da 3.1 e se o lojista vende fiado)*
```
Tarefa 3.3: Módulo customers (pasta nova): Customer (nome, telefone, documento opcional, limite de crédito), casos de uso
CreateCustomer, UpdateCustomer e consulta por nome/telefone, com permissões customer.*. Forma de pagamento "Fiado" no sales,
que gera uma receivable no treasury via evento SaleCompleted, com adaptador ligado no bootstrap (sem import direto entre módulos).
Guarde só os dados necessários (LGPD). Atualize o .importlinter.
Testes: duas empresas; venda fiada acima do limite é recusada; recebimento baixa a receivable.
```

### Fase 4: Relatórios, Backup e Fiscal

```
Tarefa 4.1: Crie o módulo backup (pasta nova): BackupService usando sqlite3.Connection.backup(), PRAGMA integrity_check,
zip com checksum SHA-256, rotação (30 diários + 12 mensais), destino secundário configurável,
gatilhos (fechamento de caixa, primeiro uso do dia, fechamento do app) e backup automático antes de qualquer migração.
Tela de restauração guiada que salva cópia do banco atual antes de sobrescrever.
Teste: backup, corromper, restaurar e comparar os dados.

Tarefa 4.2: Crie o módulo reports (pasta nova): vendas por período/produto/operador, estoque baixo, margem, DRE simples,
fechamento de caixa. Exportação CSV e PDF. Consultas agregadas direto em SQL (sem carregar entidades).
Imports pesados (PDF) feitos de forma lazy. Respeita o filtro por company_id e as permissões.

Tarefa 4.3: Crie o módulo fiscal (pasta nova) contendo apenas a interface FiscalPort (Protocol) em application/ports.py
e um teste provando que o fluxo de venda não depende de nenhum adaptador fiscal. Sem emissão de documentos.
Atualize o README para dizer exatamente isso.
```

**Tarefa 4.4: Importação de produtos por CSV** *(nova: facilita a migração de quem já tem planilha)*
```
Tarefa 4.4: Importação de produtos por CSV. Tela com pré-visualização e validação linha a linha (SKU ou código de barras
duplicado, preço não numérico, vírgula decimal pt-BR) e relatório de erros. Converta preços para centavos com Decimal, nunca float.
A importação roda em UMA transação (tudo ou nada), com a opção explícita de pular linhas inválidas. Permissão product.import e
auditoria do lote. Testes com CSV de exemplo em UTF-8 e em Latin-1, e teste de duas empresas.
```

### Fase 5: Endurecimento

```
Tarefa 5.1: Script de carga que gera 50 mil produtos e 100 mil vendas; meça abertura do app, busca no PDV e
fechamento de caixa. Aponte gargalos e crie os índices necessários via migração nova.

Tarefa 5.2: Tratamento global de exceções (log + mensagem amigável + opção de copiar o relatório de erro),
revisão de segurança (nenhuma regra de permissão só na UI, senhas nunca em log, evidência por grep/teste
para cada item), teste de migração da versão N-1 para N com dados reais, e documentação do usuário em docs/
(instalação em 5 minutos, primeiro uso, backup).

Tarefa 5.3: Verificação real de empacotamento. Gere o build com PyInstaller em Windows 10+ e em Linux, confirme que
os scripts de migração e os plugins Qt estão no pacote, e faça um teste de inicialização do executável com banco
novo e com banco de versão anterior. Gere e teste o instalador Inno Setup, o .deb e o AppImage. No Linux, teste em Wayland e em X11
(QT_QPA_PLATFORM=wayland e =xcb), confirme que o logo e a tela de login aparecem sem artefatos e que o pacote traz as
bibliotecas do Qt necessárias (por exemplo libxcb-cursor no X11). Registre o que foi testado em cada SO e o que não foi.
```

---

## Fase C: Correções de qualidade (faça ANTES da Tarefa 2.3)

Resultado da auditoria de 18/10/2026. Um prompt por vez, cada um em chat novo, na ordem abaixo. Crie uma branch antes e faça o commit do trabalho atual (`git switch -c correcoes`). A C.7 e a C.8 foram acrescentadas em 20/10/2026. A C.1 e a C.2 são independentes: se preferir uma base verde antes de limpar arquivos, faça a C.2 primeiro.

**C.1 Limpeza de arquivos vazios e inúteis**
```
Releia o CONTEXTO.md. Tarefa de limpeza (não avance para 2.3). Remova SOMENTE estes itens aprovados:
- src/erp/modules/backup/, receipts/, reports/ (placeholders sem código; voltam nas tarefas 4.1, 2.4 e 4.2)
- src/erp/modules/fiscal/ (antes: `grep -rn "FiscalPort" src tests`; se não existir, corrigir a frase do README; volta na 4.3)
- src/erp/modules/pricing/infrastructure/
- src/erp/modules/cash/presentation/ e treasury/presentation/ (voltam nas tarefas 2.2.1 e 3.2)
- src/erp/modules/pricing/application/ports.py (antes: confirme por busca, inclusive imports relativos, que nada o usa)
- codigo_para_analise.md
Não toque em sales/presentation/. Atualize .importlinter, alembic/env.py, bootstrap.py, pyinstaller.spec e pyproject.toml
para não citarem o que foi removido. Falhas anteriores (bootstrap do audit, testes de login, import-linter)
devem ser listadas como pré-existentes, sem corrigi-las aqui. Rode o critério de pronto e termine com `git status --short`.
```

**C.2 Bug do bootstrap e testes de login**
```
Releia o CONTEXTO.md. Duas correções, nada além disso:
1) src/erp/modules/audit/infrastructure/triggers.py: _BYPASS_TABLE_DDL tem 2 statements numa chamada de execute(),
   o que o sqlite3 do Python 3.12 rejeita. Separe em execute() distintos na mesma transação (sem executescript,
   sem dividir por ";"). Verifique se outros DDLs têm o mesmo problema.
   Testes: banco vazio cria audit_bypass com id=1; segunda execução é idempotente; os triggers existem e
   bloqueiam UPDATE/DELETE em audit_logs quando o bypass está desligado.
2) AuthenticateOutput agora exige company_id: corrija os fakes em tests/unit/modules/identity/test_login_presenter.py
   e tests/ui/test_login.py, usando company_id realista em pelo menos um teste por arquivo, e adicione um teste
   de que o login propaga company_id para CurrentSession.
Pronto quando o critério de pronto passar, com as saídas reais.
```

**C.3 Alinhar o import-linter à regra do projeto**
```
Releia o CONTEXTO.md. Ajuste o .importlinter para impor exatamente a regra: um módulo só importa o application/
público de outro módulo; é proibido importar domain, infrastructure e presentation de outro módulo.
Depois corrija só as violações reais: companies/permission_gate.py importando identity.domain.user, e sales e
pricing importando catalog.infrastructure ou serviços concretos do catalog. Use ports e adaptadores no bootstrap.py,
ou gate de permissão compartilhado em shared/application. Verifique se há gates de permissão duplicados.
Antes de mexer em sales, explique em 3 linhas por que ele usa o UnitOfWork do catalog (transação compartilhada?)
e NÃO altere a semântica transacional sem me perguntar.
Pronto quando `uv run import-linter lint` passar e uma violação inserida de propósito fizer o lint falhar.
```

**C.4 Provar isolamento multiempresa e segurança**
```
Releia o CONTEXTO.md. Para cada item, entregue evidência (grep, trecho de código ou teste), não apenas "seguro":
- Toda query de repositório de tabela com company_id filtra por ele? Escreva testes com duas empresas.
- Cada caso de uso protegido checa permissão no limite da aplicação?
- Liste todo uso de text() ou SQL montado por f-string/concatenação e diga se há entrada externa.
- Nenhum log recebe senha ou password_hash.
- Descreva em 3 linhas o risco de a tabela audit_bypass permitir desligar a auditoria a quem tem acesso ao arquivo
  do banco, e se é aceitável. Apenas descreva, sem mudar.
Corrija apenas o que provar estar errado.
```

**C.5 Padrão único de datetime (investigar e parar)**
```
Releia o CONTEXTO.md. NÃO altere nada ainda. Verifique se TimestampMixin (server_default=func.now()) é usado por algum model
e quais models usam UTCDateTime com default em Python. Proponha o menor plano para ter um único padrão UTC aware,
incluindo a migração Alembic nova (modo batch) se o schema mudar e testes de ida e volta com datetimes aware.
Nunca edite migrações antigas. Pare e aguarde minha aprovação.
```

**C.6 Formatação e README**
```
Releia o CONTEXTO.md. Rode `uv run ruff format .` sozinho, mostre `git diff --stat` e confirme que mypy e testes seguem iguais.
Depois atualize só o README: tabela de status conforme o que está implementado e testado; instalação para Windows
(PowerShell) e Linux usando `uv run`, sem a linha duplicada de execução; incluir `ruff format --check`; não fixar a
lista de migrações; comandos de build por SO. Acrescente uma nota no topo do Roadmap registrando as decisões reais
(PySide6, Python 3.12+, Windows 10+), sem reescrevê-lo. Não mude os SO suportados.
```

**C.7 Tela de login: logo no build e artefato visual no Wayland**
```
Releia o CONTEXTO.md (seção UI Qt). Corrija SOMENTE a tela de login e o carregamento do logo no build. Nada além disso.
1) Crie src/erp/shared/ui/resources.py com resource_path(*parts) -> Path: usa sys._MEIPASS/"erp" quando congelado e a pasta
   do pacote erp em desenvolvimento.
2) Reescreva src/erp/modules/identity/presentation/login_view.py: janela normal (sem FramelessWindowHint e sem
   WA_TranslucentBackground); card centralizado em um QGridLayout, com um QFrame VAZIO atrás só para a sombra
   (QGraphicsDropShadowEffect nesse frame, nunca no card); estilo em um único QSS por objectName; logo via resource_path,
   com log de aviso e sem quebrar se o arquivo faltar; botão Entrar como default; mesmo contrato com o presenter
   (set_presenter, show_error, clear_password). Cada widget e cada layout é criado UMA vez.
3) packaging/pyinstaller.spec: logo em datas (destino erp/ui/resources), falha clara se o arquivo não existir e upx=False
   (UPX pode corromper bibliotecas do Qt).
4) Testes (QT_QPA_PLATFORM=offscreen): resource_path em dev e com sys._MEIPASS simulado via monkeypatch; o diálogo não tem
   FramelessWindowHint nem WA_TranslucentBackground; o logo carrega (pixmap não nulo); o botão chama presenter.login com
   usuário e senha.
Pronto quando o critério de pronto passar. A verificação visual (Fedora, wayland e xcb, com o executável do PyInstaller) é minha:
marque-a como "não executado" se você não puder testar. Se o quadrado branco persistir, isole a splash antes de mexer no login.
```

**C.8 Senha padrão `admin/admin` (investigar e parar)**
```
Releia o CONTEXTO.md. NÃO altere nada ainda. O login admin/admin funciona, o que viola "não existe senha padrão".
Rode `grep -rniE "admin.?admin|\"admin\"" src tests alembic` e mostre onde o usuário admin e a senha são criados
(seed, bootstrap, migração, testes, scripts). Diga se algum hash ou senha está em migração já aplicada (nunca editar migração
aplicada). Proponha o menor plano: (a) primeiro uso: se não existe nenhum usuário, uma tela de "Primeiro uso" cria o
administrador com senha que cumpra a política do identity, must_change_password=True, ou lê NEXOERP_ADMIN_PASSWORD;
(b) o que fazer com o banco de desenvolvimento que já tem admin/admin (migração nova que force a troca, ou recriar o banco).
Nunca registrar senha nem hash em log. Pare e aguarde minha aprovação.
```

---

## Passo 3: Prompts de apoio (use quando precisar)

**Revisão após cada tarefa**
```
Revise o código que você acabou de gerar contra o CONTEXTO.md. Liste violações das regras de dependência,
imports de outro módulo fora do application/, uso de float em dinheiro, datetime sem timezone, regras de negócio
na UI, permissões não verificadas no caso de uso, falta de transação, falta de teste de duas empresas,
arquivos ou pastas vazias criados sem necessidade e falta de testes. Corrija cada item apontado e mostre
apenas os arquivos alterados, com o resultado real do critério de pronto.
```

**Quando ocorrer erro**
```
Ao rodar `<comando>` apareceu este erro:
<cole o traceback completo>
Explique a causa em 2 linhas e corrija mostrando só os arquivos alterados. Não mude a arquitetura.
```

**Quando a IA "esquecer" o contexto**
```
Releia o CONTEXTO.md. Seu último código violou: <regra>. Refaça a tarefa respeitando essa regra.
```

**Quando a IA repetir blocos de código ou travar em loop**
```
Sua última resposta repetiu blocos de código (ou ficou grande demais). Descarte-a. Reescreva SOMENTE o arquivo <caminho>,
uma única vez, sem trechos duplicados. Depois rode `uv run ruff check <caminho>` e `uv run python -m py_compile <caminho>`
e mostre a saída real.
```

**Varredura de arquivos vazios (rodar a qualquer momento)**
```
uv run python scan_stubs.py
```
O script só lê o repositório e lista arquivos e pastas sem código real. Depois, peça à IA que confirme
cada candidato por busca (inclusive imports relativos e dinâmicos) antes de qualquer remoção.

---

## Dicas práticas

- **Modelo:** use o modelo de código mais forte que seu orçamento permitir. Modelos menores erram mais em SQLAlchemy 2.0 e Qt.
- **Contexto longo:** em conversas muito longas o modelo degrada. Inicie um chat novo a cada tarefa e cole apenas o `CONTEXTO.md`, mais os arquivos relevantes já existentes (por exemplo, os ports do módulo que vai ser consumido).
- **Versionamento:** crie uma branch e faça um commit por tarefa (`feat(catalog): ...`). A IA nunca commita. Se ela quebrar algo, você reverte sem perder o resto.
- **Valide o que ela afirma:** modelos às vezes inventam métodos de biblioteca e relatam sucesso sem rodar nada. Peça sempre as saídas reais dos comandos e rode você mesmo na dúvida.
- **Revise você mesmo os pontos críticos:** Money, UnitOfWork, auditoria, fechamento de caixa e backup. São onde um bug custa dinheiro real ao lojista.
- **Ordem importa:** não pule a Tarefa 1.4 (auditoria) para depois do catálogo, pois adaptar auditoria depois é bem mais caro.
- **Não crie estrutura vazia:** pastas e arquivos nascem junto com o código que os usa. Placeholder vazio vira ruído e quebra contratos do import-linter.
- **Ao concluir cada fase:** rode a Tarefa 5.3 (build real) pelo menos uma vez por fase grande, para não descobrir só no final que o empacotamento quebrou.
- **Sinais de que a IA se perdeu:** arquivo gigante, o mesmo bloco repetido, comando de shell dentro do código (como um `EOF` solto) ou a resposta terminando no meio. Não tente remendar: descarte e peça o arquivo de novo, só ele. Rode `ruff check` e `py_compile` no arquivo antes de testar qualquer coisa.
- **Linux (Wayland e X11):** teste sempre com `QT_QPA_PLATFORM=wayland` e `QT_QPA_PLATFORM=xcb`. Se uma janela mostrar quadrado branco ou texto sumido, procure primeiro por `FramelessWindowHint`, `WA_TranslucentBackground` e `QGraphicsEffect` em container; a splash também é uma janela sem borda e merece suspeita.
- **Senha de desenvolvimento:** se algo só funciona com `admin/admin`, trate como bug de segurança, não como atalho. A regra do projeto é não ter senha padrão.
