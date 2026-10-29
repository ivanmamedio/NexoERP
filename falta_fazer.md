Data: 23/10/2026  
Branch: tarefa-4.1-backup (commit ee65bb9)  
Base: Comparação entre Roadmap_ERP_Pequenos_Comercios_Windows7_Debian.md, Tasks.md, correcoes_NexoERP_para_nemotron.md e o estado atual do repositório.
1. Resumo Executivo
O projeto está muito avançado em relação ao roadmap original. A maioria das fases 0, 1 e 2 (core) está implementada e testada. As correções da correcoes_NexoERP_para_nemotron.md (logo, login, build) já foram aplicadas e validadas.
Estado dos testes/qualidade:
Check	Status
pytest	✅ 288 passed
ruff check	✅ All passed
ruff format --check	✅ 439 files formatted
import-linter	✅ 2 contracts kept, 0 broken
mypy	⚠️ 25 erros no módulo receipts (dependências externas sem stubs)
PyInstaller build	✅ Gera dist/ERP/ERP com logo em _internal/erp/ui/resources/logo.png
2. Análise por Documento
2.1 correcoes_NexoERP_para_nemotron.md — CONCLUÍDO ✅
Correção	Status	Evidência
1. Helper resource_path unificado	✅	src/erp/ui/resource_paths.py + re-export em shared/ui/resources.py
2. pyinstaller.spec com logo	✅	datas inclui (LOGO_PATH, "erp/ui/resources") + validação pré-build
3. login_view.py sem duplicação/transparência	✅	Removidos widgets duplicados; sem FramelessWindowHint/WA_TranslucentBackground
4. Splash screen usa helper	✅	src/erp/ui/splash/__init__.py importa resource_path
5. Testes de regressão	✅	14 testes de login/recursos passam
Verificação manual pendente: Teste visual no Fedora/Wayland (artefato branco) — não executável no ambiente headless atual.
2.2 Tasks.md — Fase C (Correções) — PARCIALMENTE CONCLUÍDO
Item	Status	Observação
C.1 Limpeza arquivos vazios	⚠️ Não aplicável	Os módulos backup, receipts, reports, fiscal têm código real (não são placeholders). pricing/infrastructure/ não existe. cash/presentation/ e treasury/presentation/ têm código. pricing/application/ports.py é interface real usada. codigo_para_analise.md não existe.
C.2 Bug bootstrap + testes login	✅ Concluído	Triggers já usam execute() separados; testes já têm company_id e testam propagação.
C.3 Import-linter alinhado	✅ Concluído	Contratos corretos: só application/ público permitido entre módulos. Violações citadas não existem.
C.4 Multiempresa + segurança	✅ Verificado	Repositórios filtram por company_id via CurrentSession. text() só com parâmetros. Senhas não em logs. audit_bypass risco documentado.
C.5 Datetime único	✅ Já consistente	TimestampMixin usa default=_utcnow + UTCDateTime (aware). Sem func.now().
C.6 Formatação + README	✅ Concluído	ruff format ok; README atualizado com status real, comandos, limitações.
C.7 Login: logo + Wayland	✅ Concluído	Implementado conforme spec. Teste visual Wayland pendente (ambiente).
C.8 Senha admin/admin	✅ Não existe	Seed não cria admin padrão. create_first_admin requer NEXOERP_ADMIN_PASSWORD. Migração 0009 força must_change_password=True em bancos legados.
2.3 Roadmap_ERP_Pequenos_Comercios_Windows7_Debian.md — Status por Fase
Fase	Roadmap	Implementado	Gap
Fase 0 Fundação	Repo, deps, janela mínima, SQLite, PyQt5/Win7, instaladores, CI	✅ Python 3.12, PySide6, SQLite WAL, Alembic, bootstrap, PyInstaller spec, CI (GitHub Actions), .deb/Inno Setup config	❌ Windows 7 (fora de escopo por decisão — PySide6/Qt6 não suporta). Build real em Windows/Linux não verificado em VM limpa.
Fase 1 Identity, Companies, Audit, Catalog, Pricing	Login, RBAC, seed, empresas, catálogo, precificação, auditoria	✅ Todos implementados (domínio, app, infra, presentation)	—
Fase 2 Caixa e PDV	Cash sessions, sangria, suprimento, fechamento, PDV teclado, comprovante, ESC/POS	✅ Domínio/app/infra de Cash e Sales/PDV implementados<br>⚠️ Telas do Caixa (cash/presentation) existem mas não listadas no roadmap como "concluídas"<br>❌ Receipts (módulo 2.4) — implementado mas roadmap diz "criar na tarefa 2.4"	 
Fase 3 Tesouraria	Payables, receivables, fluxo de caixa, categorias	✅ Domínio/app/infra + subscribers (livro-razão).<br>⚠️ treasury/presentation existe (cash_flow_presenter) mas roadmap diz "criar na 3.2"	 
Fase 4 Relatórios, Backup, Fiscal	Reports (CSV/PDF), Backup (sqlite3.backup, rotação), FiscalPort	✅ Backup e Reports implementados (domínio, app, infra, presentation).<br>✅ Fiscal — apenas FiscalPort (Protocol) como especificado.	 
Fase 5 Endurecimento	Carga 50k/100k, exceções, segurança, build real Windows/Linux	❌ Não iniciado	 
2.4 Tarefas Explícitas no Tasks.md — Status Detalhado
Tarefa	Descrição	Status
0.1–0.3	Fundação, núcleo, Alembic/bootstrap	✅
0.4	Empacotamento CI	✅ Configurado (build real não testado em VM)
1.1–1.6	Identity, Companies, Audit, Catalog, Pricing	✅
1.2	Identity telas	✅ (login, users, change_password, first_use)
1.3	Companies	✅
1.4	Audit	✅
1.5	Catalog	✅
1.6	Pricing	✅
1.7	Configurações (NOVA)	✅ Implementada (settings module com company_id, receipt header/footer, session timeout)
2.1	Cash (domínio/casos de uso)	✅
2.2.1	Telas do Caixa (NOVA)	✅ Implementada (cash/presentation existe com open/close/sangria/suprimento/closing_report)
2.2	Sales (domínio/casos de uso)	✅
2.3	Tela PDV	✅ Implementada (pos_view.py, pos_presenter.py — teclado, multiplicador, pagamento misto, PIN supervisor)
2.4	Receipts	✅ Implementada (gerador, preview, ESC/POS, Windows spooler, CUPS, settings) — roadmap diz "criar na 2.4"
2.5	Compras/Inventário (NOVA)	✅ Implementada (purchases module com RegisterPurchase, CountInventory)
3.1	Treasury	✅ (parcial — falta UI completa, tem cash_flow_presenter)
3.2	Fluxo de caixa UI (NOVA)	⚠️ Parcial (treasury/presentation só tem cash_flow_presenter)
3.3	Clientes/Fiado (NOVA, opcional)	✅ Implementada (customers module)
4.1	Backup	✅
4.2	Reports	✅
4.3	FiscalPort	✅ (apenas Protocol)
4.4	Import CSV (NOVA)	✅ Implementada (import_csv module)
5.1–5.3	Endurecimento	❌ Não iniciado
3. Problemas Identificados (Não cobertos nos docs acima)
3.1 Mypy — 25 erros no módulo receipts (P2)
- Causa: Dependências externas sem stubs (escpos, win32print, cups) + tipos dinâmicos Qt.
- Impacto: Não bloqueia funcionalidade core. Módulo receipts é fase futura (2.4).
- Ação sugerida: Adicionar # type: ignore seletivos ou instalar stubs quando for trabalhar no módulo.
3.2 Build Real em Windows/Linux não validado (P1)
- Roadmap exige teste em VM limpa Windows 10+ e Linux Debian/Ubuntu mínimo.
- CI configura windows-latest e ubuntu-22.04 mas não testa instalação/desinstalação/preservação de dados.
3.3 Teste Visual Wayland/Fedora (P1)
- Correção C.7 feita, mas validação visual do artefato branco não executável no ambiente headless.
- Necessário testar em Fedora/Wayland real.
3.4 Módulos "Adiantados" vs Roadmap
Os módulos receipts, purchases, import_csv, customers, settings, backup, reports estão implementados mas o roadmap original os colocava em fases futuras. Isso não é um problema técnico, mas a documentação (README, Tasks.md) deve refletir a realidade.
4. Recomendações Prioritárias
Prioridade	Ação	Esforço
P0	Testar build PyInstaller em VM Windows 10+ limpa e Linux (Debian/Ubuntu)	Médio
P0	Validar tela de login no Fedora/Wayland real (artefato branco)	Baixo (requer HW/VM)
P1	Resolver mypy no módulo receipts quando for trabalhar nele (Task 2.4)	Baixo
P1	Executar Tarefa 5.3 (build real + smoke test) antes de release	Médio
P2	Atualizar Tasks.md e Roadmap para refletir módulos já implementados (receipts, purchases, import_csv, customers, settings)	Baixo
P3	Considerar remover pricing/application/ports.py se não for mais usado (verificar)	Baixo
5. Decisões Necessárias do Usuário
1. Windows 7: Roadmap original previa suporte, mas decisão técnica adotou PySide6/Qt6 (Windows 10+). Confirmar que Windows 7 está definitivamente fora de escopo? (Já refletido no README)
2. Módulos adiantados: receipts, purchases, import_csv, customers, settings estão prontos. Deseja que eu atualize a documentação (Tasks.md, Roadmap) para marcar como concluídos?
3. Mypy receipts: Quer que eu adicione # type: ignore seletivos para zerar mypy agora, ou deixa para quando for trabalhar no módulo 2.4?
4. Teste em VM: Quer que eu prepare scripts/instruções para validar o build em Windows/Linux, ou você fará manualmente?
6. Arquivos-chave para Próximos Passos
Se autorizar continuidade, os próximos itens lógicos (conforme Tasks.md) seriam:
1. Fechar 2.2/2.3 — Já implementados (PDV + Sales)
2. 1.7 Configurações — Já implementado (settings module)
3. 2.4 Receipts — Já implementado (precisa mypy fix)
4. 2.5 Compras/Inventário — Já implementado
5. 3.1 Treasury — Completar (já tem domínio/app/infra)
6. 3.2 Fluxo de Caixa UI — Completar treasury/presentation
7. 4.1–4.4 — Já implementados
8. 5.x Endurecimento — Iniciar
Pronto para prosseguir? Indique quais itens deseja que eu aborde (ex: corrigir mypy receipts, atualizar documentação, preparar teste VM, etc.) e eu executo.
