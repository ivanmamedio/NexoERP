# ERP Desktop Open Source para Pequenos Comércios

> **Nota de decisões reais (20/10/2026):** o projeto adota **PySide6 (Qt 6 Widgets, sem QML)**, **Python 3.12+** e suporta **Windows 10+ e Linux** (baseado em Debian/Ubuntu). Windows 7 está fora de escopo. O Roadmap abaixo mantém o planejamento original de compatibilidade legada como referência histórica, mas as decisões de implementação seguem a stack acima.

## Arquitetura, compatibilidade legada e roadmap de desenvolvimento

**Objetivo:** desenvolver um sistema de gestão comercial desktop,
gratuito e de código aberto, voltado a pequenos comércios em geral, com
funcionamento offline e prioridade explícita para **Windows 7 e Linux
baseado em Debian**.

**Princípio central:** manter uma única base de código para as regras de
negócio e adaptar apenas as integrações e o empacotamento específicos de
cada sistema operacional.

> **Aviso de compatibilidade e segurança:** Windows 7 e Python 3.8 estão
> fora de suporte. A compatibilidade com Windows 7 deve ser tratada como
> requisito legado, validado em máquinas reais ou virtuais. Não prometer
> segurança equivalente à de sistemas operacionais atualizados. Para
> operações comerciais conectadas à internet, recomendar sistema
> operacional suportado sempre que possível.

------------------------------------------------------------------------

## 1. Requisitos e prioridades

### 1.1 Requisitos obrigatórios

1.  Compatibilidade prioritária com Windows 7 de 32 ou 64 bits, conforme
    a viabilidade demonstrada nos testes.
2.  Compatibilidade com distribuições Linux baseadas em Debian, com
    versões mínimas explicitamente documentadas.
3.  Aplicativo desktop instalável, com interface em português do Brasil.
4.  Funcionamento offline para operações centrais: cadastros, estoque,
    caixa, vendas, financeiro e relatórios.
5.  Banco de dados local, sem exigir servidor ou conexão com a internet.
6.  Instalação simples para usuários sem conhecimento técnico.
7.  Código aberto publicado no GitHub, com suporte, treinamento,
    instalação e customizações como possíveis fontes de receita.
8.  Proteção de dados comerciais, permissões por função, auditoria,
    backup e restauração.
9.  Testes de compatibilidade e empacotamento desde o primeiro
    protótipo.
10. Não depender de serviços pagos para compilar, testar ou distribuir a
    versão básica.

### 1.2 Metas de qualidade

-   Inicialização rápida em hardware antigo; meta inicial inferior a 3
    segundos em uma máquina de referência definida e documentada.
-   Uso de memória medido em equipamentos reais, em vez de assumir um
    valor universal.
-   Não perder vendas ou movimentos de estoque em caso de erro durante
    uma transação.
-   Backup restaurável e testado.
-   Instalação e atualização sem sobrescrever os dados do usuário.
-   Ações críticas sujeitas a autorização e trilha de auditoria.
-   Interface utilizável por teclado, especialmente no PDV.

### 1.3 Limites importantes

-   O sistema não deve ser apresentado como emissor fiscal enquanto não
    houver implementação e validação fiscal específica.
-   O aplicativo não pode garantir que um computador comprometido, um
    administrador do sistema ou alguém com acesso direto ao banco nunca
    altere dados.
-   Impressoras, gavetas e periféricos variam. O suporte deve ser
    validado por modelo, conexão e sistema operacional.
-   Compatibilidade com Windows 7 não significa que todos os
    componentes, drivers, protocolos TLS ou serviços de terceiros
    continuarão funcionando indefinidamente.

------------------------------------------------------------------------

## 2. Stack tecnológica e estratégia de compatibilidade

### 2.1 Estratégia recomendada: uma base de código, builds separados

A camada de domínio e os casos de uso devem ser compartilhados. Os
builds do Windows legado e do Linux devem ser gerados separadamente,
usando versões de dependências testadas para cada destino.

  -------------------------------------------------------------------------
  Camada                  Diretriz                  Motivo
  ----------------------- ------------------------- -----------------------
  Linguagem               Python, com versões       Desenvolvimento rápido,
                          fixadas por alvo          comunidade ampla e uma
                                                    linguagem principal

  Interface desktop       PyQt5 com versão do Qt 5  Widgets maduros para
                          validada para Windows 7   tabelas, formulários,
                                                    atalhos e PDV

  Banco local             SQLite                    Sem servidor, funciona
                                                    offline e simplifica
                                                    instalação e backup

  ORM                     SQLAlchemy 2.x em versão  Repositórios e
                          compatível com o Python   transações organizados
                          selecionado               

  Migrações               Alembic em versão         Atualizar esquemas sem
                          compatível com o Python e apagar dados
                          SQLAlchemy escolhidos     

  Hash de senhas          bcrypt em versão          Armazenamento de senhas
                          compatível, ou            com hash lento
                          alternativa validada      

  Impressão ESC/POS       Biblioteca Python         Impressoras térmicas de
                          compatível com o          58/80 mm
                          ambiente; abstração       
                          própria de impressão      

  Caminhos de dados       `platformdirs` em versão  Guardar dados fora da
                          compatível ou adaptador   pasta de instalação
                          próprio                   

  Empacotamento Windows   PyInstaller em versão     Instalador `.exe`
                          testada + Inno Setup      

  Empacotamento Linux     PyInstaller ou            Pacote instalável em
                          empacotamento nativo,     sistemas Debian
                          mais ferramenta para      
                          `.deb`                    

  Testes                  pytest; testes de         Validar regras,
                          interface quando          integrações e
                          compatíveis               regressões

  Qualidade               Ruff/mypy/import-linter   Consistência e limites
                          somente em versões        arquiteturais
                          compatíveis com o         
                          ambiente de               
                          desenvolvimento           

  CI                      GitHub Actions para       Automatizar o que for
                          testes e builds           possível sem fingir que
                          compatíveis, mais testes  runners modernos
                          manuais em VM             reproduzem Windows 7
  -------------------------------------------------------------------------

### 2.2 Windows 7: linha legada

**Não usar PySide6 como interface-alvo do Windows 7.** PySide6/Qt 6
requer versões mais recentes do Windows e não atende a esse requisito.

A hipótese inicial para o protótipo é:

-   Python 3.8, preferencialmente uma distribuição binária que
    comprovadamente execute no Windows 7.
-   PyQt5 associado a uma versão do Qt 5 cuja documentação e testes
    confirmem suporte ao Windows 7.
-   PyInstaller em versão compatível com a versão do Python e com o
    Windows-alvo.
-   Instalador criado com Inno Setup em versão testada no Windows 7.
-   Dependências fixadas e guardadas em um arquivo de lock ou lista de
    versões reproduzível.

**Atenção:** Python 3.8 encerrou o suporte em outubro de 2024. O fato de
uma versão funcionar no Windows 7 não significa que receba correções de
segurança. Antes de escolher versões definitivas, criar um protótipo e
validar a cadeia inteira: Python, Qt, PyQt5, SQLite, criptografia, TLS,
impressão e instalador.

PyQt5 possui termos de licença próprios (GPL ou licença comercial),
diferentes da LGPL do Qt. Se a distribuição do projeto for GPLv3,
validar a compatibilidade da versão selecionada e cumprir todas as
obrigações de distribuição. Não presumir que PyQt5 pode ser distribuído
sob MIT ou outra licença permissiva. Registrar a decisão de
licenciamento no repositório antes de publicar binários.

### 2.3 Linux baseado em Debian

O Linux deve ser desenvolvido e empacotado em um ambiente Linux
compatível com a versão mínima que será suportada. A versão exata mínima
de Debian/Ubuntu/Linux Mint deve ser definida e registrada após testes.

Diretrizes:

-   Gerar o pacote `.deb` em ambiente controlado.
-   Para binários empacotados com PyInstaller, compilar em uma base tão
    antiga quanto a mínima suportada, porque a compatibilidade de glibc
    normalmente não é garantida no sentido inverso.
-   Testar instalação, inicialização, permissões de arquivos, fontes,
    impressão via CUPS/USB/rede e desinstalação sem apagar dados do
    usuário.
-   Declarar dependências de bibliotecas de sistema necessárias.
-   AppImage pode ser oferecido como alternativa, mas não substitui a
    exigência do `.deb`.
-   Não presumir que uma versão de Python adequada ao Windows 7 esteja
    instalada no Linux; os builds devem ser independentes.

### 2.4 Dependências e compatibilidade

-   Fixar versões em arquivos de dependências e registrar as versões
    usadas para gerar cada release.
-   Não atualizar bibliotecas automaticamente sem executar a suíte de
    testes.
-   Preferir dependências mantidas e necessárias; evitar adicionar
    bibliotecas sem benefício claro.
-   Manter uma lista de componentes legados e seus riscos.
-   Separar as dependências comuns das específicas de Windows e Linux.
-   Testar importação de dados e migrações com bancos criados por
    releases anteriores.

### 2.5 Alternativas consideradas

-   **PySide6/Qt 6:** não atende ao Windows 7; pode ser reconsiderado
    apenas se a compatibilidade legada deixar de ser obrigatória.
-   **Electron/Tauri:** adicionam runtimes e/ou linguagens e aumentam a
    complexidade para esse objetivo.
-   **Tkinter:** pode ser um plano alternativo caso a cadeia PyQt5/Qt 5
    não seja viável; validar aparência, tabelas, impressão e desempenho
    antes de decidir.
-   **Interface web local:** não deve ser adotada sem avaliar o
    navegador disponível no Windows 7, que pode estar desatualizado e
    vulnerável.

------------------------------------------------------------------------

## 3. Arquitetura

### 3.1 Estilo

Adotar **monólito modular com Clean Architecture pragmática**. Não
começar com microsserviços: o sistema é local, precisa ser fácil de
instalar e manter e deve operar sem infraestrutura externa.

A direção das dependências é:

1.  `presentation` depende de `application`.
2.  `application` depende de `domain`.
3.  `infrastructure` implementa contratos definidos pelas camadas
    internas.
4.  `domain` não importa bibliotecas de UI, banco, sistema operacional
    ou impressão.

``` text
┌─────────────────────────────────────────────┐
│ presentation: telas, widgets e presenters  │
├─────────────────────────────────────────────┤
│ application: casos de uso, DTOs e ports     │
├─────────────────────────────────────────────┤
│ domain: entidades, regras e value objects   │
├─────────────────────────────────────────────┤
│ infrastructure: SQLite, ORM, impressão, FS │
└─────────────────────────────────────────────┘
```

### 3.2 Decisões importantes

-   **Dinheiro:** armazenar valores monetários em centavos (`int`) por
    meio de um value object `Money`. Não usar `float` para dinheiro.
-   **Quantidades:** para produtos por peso, definir uma escala
    documentada (por exemplo, gramas ou milésimos de unidade) ou usar
    `Decimal` com regras explícitas.
-   **Transações:** usar Unit of Work e repositórios. Venda, pagamentos,
    baixa de estoque, movimentação financeira e auditoria devem ser
    consistentes dentro das transações apropriadas.
-   **Eventos internos:** um barramento síncrono em memória pode
    desacoplar módulos, mas não substitui transações persistentes nem
    deve ser usado para garantir efeitos externos que possam falhar.
-   **Multiempresa:** manter `company_id` nas tabelas de negócio e
    filtrar por empresa ativa em todos os repositórios. Cobrir com
    testes para impedir vazamento entre empresas.
-   **Permissões:** RBAC com permissões granulares verificadas no caso
    de uso, nunca apenas escondendo botões.
-   **Fiscal:** definir uma interface `FiscalPort` para futura
    integração, sem afirmar que o sistema já cumpre obrigações fiscais.
-   **UI:** adotar MVP/MVVM leve. Views exibem e capturam eventos;
    presenters ou controladores chamam casos de uso. Regras de negócio
    devem ser testáveis sem abrir janelas.
-   **Portabilidade:** isolar impressão, abertura de gaveta, caminhos de
    arquivos, integração com spooler/CUPS, atualizador e funções
    específicas de cada SO atrás de interfaces.
-   **Falhas:** transações devem ser revertidas quando uma etapa crítica
    falhar; erros devem ser registrados sem expor senhas, PINs ou dados
    sensíveis nos logs.

### 3.3 Estrutura de pastas sugerida

``` text
meu-erp/
├── pyproject.toml
├── requirements/
│   ├── common.txt
│   ├── windows-legacy.txt
│   └── linux.txt
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── packaging/
│   ├── pyinstaller/
│   │   ├── windows.spec
│   │   └── linux.spec
│   ├── windows/
│   │   └── installer.iss
│   └── linux/
│       ├── nfpm.yaml
│       ├── app.desktop
│       └── icons/
├── migrations/
├── docs/
│   ├── architecture.md
│   ├── compatibility.md
│   ├── backup-restore.md
│   ├── threat-model.md
│   └── user-guide.md
├── src/
│   └── erp/
│       ├── __main__.py
│       ├── bootstrap.py
│       ├── config/
│       │   ├── settings.py
│       │   ├── paths.py
│       │   └── logging_config.py
│       ├── shared/
│       │   ├── domain/
│       │   ├── application/
│       │   ├── infrastructure/
│       │   └── ui/
│       ├── platform/
│       │   ├── windows/
│       │   └── linux/
│       ├── modules/
│       │   ├── identity/
│       │   ├── companies/
│       │   ├── catalog/
│       │   ├── pricing/
│       │   ├── cash/
│       │   ├── sales/
│       │   ├── treasury/
│       │   ├── receipts/
│       │   ├── audit/
│       │   ├── backup/
│       │   ├── reports/
│       │   └── fiscal/
│       └── app/
└── tests/
    ├── unit/
    ├── integration/
    ├── compatibility/
    └── ui/
```

### 3.4 Regras para contribuidores

-   Um módulo só deve consumir a API pública `application` de outro
    módulo; não importar diretamente sua `infrastructure`.
-   Aplicar `import-linter` ou verificações equivalentes quando
    compatíveis com a stack.
-   Não acessar o banco diretamente a partir das telas.
-   Toda alteração de esquema exige migração e teste.
-   Toda operação crítica deve ter testes de sucesso, falha e rollback.
-   Não incluir dados reais de clientes, bancos de produção, senhas,
    tokens ou arquivos de backup no Git.

------------------------------------------------------------------------

## 4. Modelagem de dados

Convenções gerais:

-   Identificadores inteiros são suficientes para o banco local inicial;
    UUID pode ser considerado se houver requisito real de sincronização
    futura.
-   Tabelas de negócio devem incluir `company_id`.
-   Incluir `created_at` e `updated_at` quando fizer sentido.
-   Usar exclusão lógica quando necessária para preservar histórico.
-   Aplicar chaves estrangeiras e índices apropriados.
-   Habilitar `PRAGMA foreign_keys=ON` em cada conexão SQLite.
-   Não depender de JSON para substituir tabelas relacionais quando
    forem necessárias consultas, integridade e índices.

### 4.1 Identidade e empresas

``` text
companies
  id, name, trade_name, tax_id, address, phone,
  receipt_header, receipt_footer

users
  id, name, username, password_hash, active,
  must_change_password, created_at, updated_at

roles
  id, name

permissions
  id, code

role_permissions
  role_id, permission_id

user_company_roles
  user_id, company_id, role_id
```

O PIN de supervisor, se implementado, deve ter hash próprio e política
de tentativas. Não guardar PIN em texto puro. Evitar PINs curtos como
único fator para operações de alto risco.

### 4.2 Catálogo e estoque

``` text
categories
  id, company_id, name, parent_id

suppliers
  id, company_id, name, tax_id, contact

products
  id, company_id, sku, name, category_id, unit,
  cost_cents, margin_pct, price_cents, min_stock,
  active, sold_by_weight

product_barcodes
  id, product_id, barcode
  UNIQUE(company_id, barcode) ou restrição equivalente

stock_movements
  id, company_id, product_id, type, quantity,
  ref_type, ref_id, user_id, reason, created_at

price_history
  id, product_id, old_price, new_price,
  old_cost, new_cost, user_id, created_at
```

O estoque atual deve ser derivado dos movimentos ou mantido em cache com
reconciliação e testes. Não permitir que um ajuste de estoque apague a
trilha de movimentos.

### 4.3 Precificação e pagamentos

``` text
payment_methods
  id, company_id, name, type, fee_pct, settlement_days

pricing_profiles
  id, company_id, tax_pct, fixed_cost_pct, default_margin_pct
```

A fórmula inicial de precificação pode ser:

``` text
preço = (custo + custos_fixos_rateados) /
        (1 - (impostos% + taxa_de_pagamento% + margem%))
```

Exemplo meramente ilustrativo: custo de R\$ 10,00, imposto de 6%, taxa
de pagamento de 3% e margem desejada de 30%:

`10 / (1 - 0,39) = R$ 16,39`.

Validar o denominador: se a soma dos percentuais for maior ou igual a
100%, bloquear o cálculo e explicar o problema. A fórmula precisa
distinguir margem de markup e deve mostrar a margem estimada. Oferecer
taxa média ponderada ou cenário conservador conforme as formas de
pagamento usadas pelo comércio.

### 4.4 Caixa e vendas

``` text
cash_registers
  id, company_id, name

cash_sessions
  id, register_id, opened_by, opened_at, opening_amount,
  closed_by, closed_at, expected_amounts, counted_amounts,
  difference, status

cash_movements
  id, session_id, type, amount, reason, user_id, authorized_by

sales
  id, company_id, session_id, number, customer_id,
  subtotal, discount, total, status, user_id, created_at

sale_items
  id, sale_id, product_id, description_snapshot,
  qty, unit_price, discount, total

sale_payments
  id, sale_id, payment_method_id, amount, change_given
```

Regras:

-   Uma sessão de caixa aberta por terminal, garantida no nível de
    aplicação e, quando possível, também pelo banco.
-   Uma venda concluída não deve ser apagada nem reescrita
    silenciosamente.
-   Cancelamentos e devoluções devem gerar registros compensatórios, com
    permissão e auditoria.
-   O fechamento deve reconciliar abertura, vendas, suprimentos,
    sangrias, estornos e troco.
-   Oferecer fechamento cego como opção para que o operador conte o
    caixa sem ver o valor esperado.
-   Pagamentos mistos devem somar o total da venda; troco não pode ser
    contabilizado como receita adicional.

### 4.5 Tesouraria e clientes

``` text
financial_categories
  id, company_id, name, kind

payables
  id, company_id, supplier_id, category_id, description,
  amount, due_date, paid_at, paid_amount, status

receivables
  id, company_id, customer_id, origin, amount,
  due_date, received_at, status

financial_entries
  id, company_id, date, type, amount, category_id,
  source_type, source_id

customers
  id, company_id, name, doc, phone
```

O livro financeiro deve permitir rastrear a origem dos lançamentos.
Evitar duplicar entradas ao reprocessar eventos ou importar dados.
Fiado/crediário pode ser implementado após o núcleo de vendas e caixa
estar estável.

### 4.6 Auditoria e configurações

``` text
audit_logs
  id, company_id, user_id, action, entity, entity_id,
  before_json, after_json, created_at, prev_hash, hash

settings
  key, value

backup_log
  id, path, size, created_at, status, checksum
```

Hash encadeado pode ajudar a detectar alterações na trilha, mas não
torna o banco inviolável: quem controla o arquivo ou o computador pode
alterar dados e tentar recalcular hashes. A auditoria deve ser descrita
como mecanismo de rastreabilidade e detecção, não como proteção
absoluta.

------------------------------------------------------------------------

## 5. Segurança, auditoria e backup

### 5.1 Segurança

-   Hash de senha com bcrypt ou algoritmo adequado, com parâmetros de
    custo documentados e bibliotecas compatíveis com cada build.
-   Não criptografar senhas de forma reversível.
-   Bloqueio temporário após repetidas tentativas de login, sem permitir
    negação de serviço fácil contra o único administrador.
-   Troca obrigatória da senha inicial; não distribuir uma senha padrão
    universal.
-   Encerramento ou bloqueio de sessão após período de inatividade
    configurável.
-   Permissões verificadas nos casos de uso.
-   Banco e arquivos de dados fora da pasta de instalação, usando
    diretórios próprios de cada sistema operacional.
-   Logs rotativos sem senhas, PINs, tokens ou informações sensíveis
    desnecessárias.
-   Validação de entrada e consultas parametrizadas por meio do ORM.
-   Dependências fixadas, atualizações revisadas e lista de riscos
    conhecidos.
-   Backups protegidos contra acesso não autorizado; se contiverem dados
    sensíveis, avaliar criptografia com uma solução mantida e
    compatível.
-   Não incluir atualizador automático privilegiado no MVP.
-   Não prometer que o hash da auditoria impede adulteração por alguém
    com controle total da máquina.

### 5.2 Limites específicos do Windows 7

-   Windows 7 não recebe suporte de segurança geral. Evitar navegação,
    e-mail e tarefas não relacionadas no mesmo computador do caixa
    quando possível.
-   Restringir conexões de rede, usar conta de usuário com privilégios
    mínimos e não expor serviços do aplicativo à rede por padrão.
-   Se o sistema precisar acessar internet, documentar que versões
    antigas de TLS, certificados e bibliotecas podem apresentar
    incompatibilidades.
-   Não criar uma falsa garantia de segurança por instalar antivírus ou
    usar senha.
-   Recomendar migração para sistema operacional suportado sempre que
    possível.
-   Publicar claramente quais builds são legados, quais dependências
    estão sem suporte e quais limitações são conhecidas.

### 5.3 Auditoria

Registrar, conforme aplicável:

-   Abertura e fechamento de caixa.
-   Descontos, cancelamentos e devoluções.
-   Alterações de preço e custo.
-   Ajustes de estoque.
-   Login, falhas de autenticação e encerramento de sessão.
-   Alterações de usuário, função e permissão.
-   Backup, restauração e migrações.
-   Alterações de configurações críticas.

Cada registro deve incluir usuário, empresa, data/hora, entidade afetada
e dados anteriores/posteriores quando apropriado. Implementar por casos
de uso/eventos de domínio, para reduzir o risco de esquecer o log.
Evitar registrar dados pessoais ou credenciais sem necessidade.

### 5.4 Backup e restauração

-   Usar a API de backup do SQLite (`sqlite3.Connection.backup`) em vez
    de copiar cegamente apenas o arquivo principal enquanto o banco está
    aberto, especialmente com WAL habilitado.
-   Fazer backup antes de migrações, atualizações e restaurações.
-   Agendar backups após fechamento de caixa, no primeiro uso do dia e
    ao encerrar o aplicativo, sem bloquear indevidamente a operação.
-   Executar `PRAGMA integrity_check` nos procedimentos de verificação.
-   Gerar checksum para detectar corrupção acidental.
-   Manter rotação configurável, por exemplo, 30 cópias diárias e 12
    mensais, ajustável pelo usuário.
-   Permitir destino secundário em pendrive ou pasta sincronizada pelo
    usuário. Não chamar isso de serviço de nuvem integrado nem garantir
    que a sincronização seja concluída.
-   A restauração deve criar uma cópia de segurança do banco atual,
    validar o backup escolhido e informar claramente o resultado.
-   Testar restauração em outra máquina e em uma instalação limpa.
-   Documentar que backup no mesmo disco não protege contra falha
    física, roubo ou ransomware.

------------------------------------------------------------------------

## 6. Pontos de atenção do domínio

### 6.1 Fiscal

-   Cupons de venda não fiscais devem exibir em destaque **"NÃO É
    DOCUMENTO FISCAL"**.
-   Documentar que o sistema básico não substitui a obrigação fiscal do
    lojista e a orientação do contador.
-   Requisitos variam por regime, estado e tipo de operação; consultar
    profissional qualificado antes de oferecer qualquer módulo fiscal.
-   Preparar `FiscalPort` para uma implementação futura, mas não
    anunciar NFC-e, SAT ou conformidade fiscal até concluir integração,
    testes e requisitos legais aplicáveis.

### 6.2 Hardware e impressão

-   Leitores USB de código de barras normalmente se comportam como
    teclado; tratar sequência rápida de caracteres seguida de Enter.
-   Impressoras térmicas podem usar ESC/POS por USB, serial ou rede, mas
    suporte depende do modelo e do driver.
-   No Windows, testar impressão via spooler e, quando necessário, modo
    RAW. Confirmar a abordagem em Windows 7.
-   No Linux, testar CUPS e dispositivos USB/rede.
-   A abertura da gaveta depende da impressora, cabo e comandos
    suportados.
-   Fornecer visualização do comprovante antes da impressão e tratamento
    de falhas.
-   A falha de impressão não deve registrar uma venda duas vezes. A
    venda concluída e o estado da impressão devem ser rastreados
    separadamente.

### 6.3 Licença e distribuição

-   Escolher a licença antes de publicar o primeiro release.
-   GPLv3 pode ser apropriada para incentivar que versões derivadas
    distribuídas permaneçam sob os termos da licença, mas não impede
    todos os usos comerciais.
-   MIT facilita reutilização, inclusive em forks proprietários, mas
    oferece menos reciprocidade.
-   PyQt5 é distribuído sob GPL ou licença comercial, e isso precisa ser
    compatível com a licença escolhida para o projeto. Verificar os
    termos exatos das versões utilizadas.
-   Incluir avisos de copyright e licenças de dependências.
-   Não copiar ícones, fontes ou bibliotecas sem verificar seus direitos
    de distribuição.

### 6.4 Modelo de receita

Distribuir o núcleo gratuitamente pelo GitHub e oferecer, sem bloquear o
uso básico:

-   Instalação e configuração.
-   Suporte remoto ou presencial.
-   Treinamento de equipe.
-   Migração e importação de planilhas.
-   Relatórios personalizados.
-   Integrações e customizações.
-   Configuração de backup e recuperação.
-   Módulos opcionais, inclusive fiscal, somente após validação técnica
    e legal.
-   Doações voluntárias, por exemplo, link "Me pague um café".

Explicar no README o que é gratuito, o que é serviço pago e quais são os
canais e horários de suporte. Não prometer suporte gratuito ilimitado.

------------------------------------------------------------------------

## 7. Empacotamento e distribuição

Empacotamento deve começar na Fase 0. Um protótipo mínimo precisa virar
instalador antes de o desenvolvimento funcional avançar.

### 7.1 Windows

-   Gerar build com PyInstaller em modo `onedir` como hipótese inicial,
    pois pode reduzir a demora de extração a cada abertura em discos
    antigos.
-   Criar instalador com Inno Setup em versão validada no Windows 7.
-   Incluir bibliotecas necessárias e ícones, atalhos, desinstalador e
    informações de versão.
-   Nunca armazenar o banco de dados dentro da pasta do executável.
-   Testar instalação sem privilégios administrativos quando possível,
    atualização, desinstalação e preservação dos dados.
-   Executar testes em Windows 7 limpo, sem Python instalado.
-   Testar antivírus e alertas de falso positivo; assinatura digital
    pode ser considerada quando houver orçamento.
-   Guardar logs de instalação e falhas sem registrar dados sensíveis.

### 7.2 Linux Debian

-   Gerar pacote `.deb` com metadados, ícone, arquivo `.desktop`,
    dependências de sistema e diretórios corretos.
-   Definir explicitamente as versões mínimas suportadas de
    Debian/Ubuntu/Linux Mint.
-   Compilar em uma base compatível com o sistema mais antigo suportado.
-   Testar instalação, atualização por cima de versão anterior,
    desinstalação e preservação dos dados.
-   Validar execução como usuário comum, sem `sudo` para tarefas
    normais.
-   Testar impressão CUPS e acesso aos dispositivos necessários.
-   AppImage pode ser disponibilizado adicionalmente, mas não substitui
    o `.deb`.

### 7.3 CI/CD e releases

-   Usar GitHub Actions para lint, testes unitários e de integração em
    ambientes compatíveis.
-   Gerar artefatos em builds separados.
-   Reconhecer que runners modernos não garantem compatibilidade com
    Windows 7; manter uma VM de testes específica.
-   Disparar release por tags versionadas, por exemplo `v1.0.0`.
-   Publicar instaladores, checksums, notas da versão, limitações
    conhecidas e instruções de instalação no GitHub Releases.
-   Não publicar build que não tenha passado pelos testes mínimos
    definidos.
-   O atualizador inicial apenas informa que existe uma nova versão,
    quando a consulta online estiver disponível e habilitada.
-   Fazer backup antes de migrações; permitir recuperação se a
    atualização falhar.
-   Não executar atualização remota privilegiada sem projeto de
    segurança específico.

------------------------------------------------------------------------

## 8. Roadmap de desenvolvimento

As estimativas são indicativas para uma pessoa trabalhando no projeto;
podem aumentar conforme os testes de compatibilidade e os feedbacks dos
lojistas.

### Fase 0 --- Fundação e prova de compatibilidade (1--2 semanas)

-   Criar repositório público e escolher licença.
-   Criar `README.md`, `CONTRIBUTING.md`, `SECURITY.md` e
    `CHANGELOG.md`.
-   Configurar ambiente de desenvolvimento no Linux Mint.
-   Criar estrutura inicial, arquivo de dependências e versões fixadas.
-   Criar janela desktop mínima.
-   Criar e abrir banco SQLite; inserir e consultar um produto de teste.
-   Validar Python + PyQt5 + Qt no Windows 7.
-   Gerar instalador `.exe` e instalar em VM limpa com Windows 7.
-   Gerar pacote `.deb` e instalar na versão Linux mínima escolhida.
-   Testar uma impressão de teste nos dois sistemas, se houver hardware
    disponível.
-   Criar testes unitários e integração inicial.
-   Criar CI para as verificações que possam ser automatizadas.
-   Documentar limitações encontradas.

**Critério de conclusão:** o protótipo abre, grava e consulta dados,
instala e desinstala nos alvos definidos e não depende de Python
previamente instalado. Não avançar para módulos extensos se a cadeia de
compatibilidade ainda estiver incerta.

### Fase 1 --- Identidade, empresas e catálogo (3--4 semanas)

-   Implementar login e gestão de sessão.
-   Implementar hash de senhas, troca obrigatória de senha inicial e
    limitação de tentativas.
-   Criar papéis e permissões granulares.
-   Criar cadastro de empresas e usuários.
-   Criar categorias, fornecedores, produtos e múltiplos códigos de
    barras.
-   Implementar movimentações de estoque e alerta de estoque mínimo.
-   Implementar histórico de preço e custo.
-   Criar assistente de precificação com validações.
-   Implementar auditoria transversal desde o começo.
-   Criar migrações e testes de upgrade do banco.

**Critério de conclusão:** usuário Caixa não consegue alterar preço sem
permissão, empresas não acessam dados umas das outras e alterações de
catálogo ficam registradas na auditoria.

### Fase 2 --- Caixa e PDV (4--5 semanas)

-   Abertura e fechamento de sessão de caixa.
-   Sangria, suprimento e conferência por forma de pagamento.
-   PDV orientado ao teclado.
-   Busca por código de barras e nome.
-   Quantidade, desconto e autorização por supervisor.
-   Pagamentos mistos e cálculo de troco.
-   Cancelamento e estorno com permissão e auditoria.
-   Comprovante 58/80 mm com visualização prévia.
-   Integração ESC/POS e abertura de gaveta, conforme hardware validado.
-   Tratamento de falhas de impressão sem duplicar vendas.

**Critério de conclusão:** um turno de caixa pode ser executado sem
depender do mouse, e o fechamento bate com os movimentos e pagamentos em
cenários automatizados.

### Fase 3 --- Tesouraria (3--4 semanas)

-   Contas a pagar e receber.
-   Parcelamento e recorrência quando aplicáveis.
-   Categorias financeiras.
-   Baixas e controle de vencimentos.
-   Integração rastreável entre vendas, caixa e lançamentos financeiros.
-   Fluxo de caixa diário e mensal.
-   Restrições de acesso por permissão.

**Critério de conclusão:** o fluxo de caixa reconcilia com vendas,
pagamentos, sangrias, suprimentos e lançamentos do período, sem
duplicidade.

### Fase 4 --- Relatórios e backup (2--3 semanas)

-   Relatório de vendas por período, produto e operador.
-   Relatório de estoque baixo.
-   Relatório de margem com critérios documentados.
-   DRE simples, claramente identificada como gerencial e não como
    substituta de escrituração contábil.
-   Exportação CSV e PDF.
-   Backup automático com rotação e checksum.
-   Verificação de integridade e restauração guiada.
-   Destino secundário configurável.

**Critério de conclusão:** restaurar um backup em outra máquina recupera
os dados esperados, e os relatórios reconciliam com os registros do
sistema.

### Fase 5 --- Endurecimento e lançamento 1.0 (3--4 semanas)

-   Testar com 50 mil produtos e 100 mil vendas como cenário de
    desempenho, medindo tempo e memória.
-   Testar em hardware antigo de referência.
-   Executar testes de interface, migração, rollback e restauração.
-   Testar falhas de energia e encerramento inesperado em ambiente
    controlado.
-   Revisar permissões e trilha de auditoria.
-   Fazer revisão das dependências e licenças.
-   Documentar instalação, atualização, backup e recuperação em
    português.
-   Criar vídeos curtos e guia de contribuição.
-   Abrir issues adequadas para iniciantes (`good first issue`).
-   Pilotar com 2--3 lojistas e recolher feedback.
-   Publicar instaladores e limitações conhecidas no GitHub Releases.

**Critério de conclusão:** instalação limpa, operação básica,
atualização e recuperação de backup passam nos testes documentados para
cada sistema suportado.

### Pós-1.0 --- Backlog possível

-   Fiado/crediário e cadastro de clientes ampliado.
-   Etiquetas de preço.
-   Importação e exportação de planilhas.
-   Módulo fiscal, após análise especializada.
-   Sincronização opcional entre lojas.
-   Criptografia do banco com solução mantida e compatível.
-   Painel multilojas.
-   Novos sistemas operacionais, caso deixem de comprometer o suporte ao
    Windows 7.

------------------------------------------------------------------------

## 9. Testes e critérios de aceitação

### 9.1 Testes funcionais

-   Criar, editar, consultar e desativar produto.
-   Registrar venda com um ou vários itens.
-   Registrar pagamentos mistos e troco.
-   Cancelar venda e conferir estornos.
-   Fechar caixa e reconciliar os valores.
-   Criar contas a pagar/receber e confirmar lançamentos.
-   Exportar relatórios e verificar totais.
-   Fazer backup, corromper uma cópia de teste e verificar detecção.
-   Restaurar backup e comparar contagens e valores.
-   Atualizar uma versão antiga sem perder dados.

### 9.2 Testes de segurança

-   Usuário sem permissão não executa operação protegida mesmo chamando
    diretamente o caso de uso.
-   Falhas de login não revelam se a senha ou o usuário específico
    estava correto.
-   Senhas e PINs não aparecem em logs.
-   Acesso a outra empresa é bloqueado.
-   Migração malsucedida não deixa o banco parcialmente atualizado sem
    possibilidade de recuperação.
-   Restauração exige confirmação e preserva cópia anterior.
-   Consultas são parametrizadas.
-   Não existe senha padrão universal.

### 9.3 Matriz mínima de compatibilidade

Manter uma tabela no repositório com:

-   Sistema operacional e edição.
-   Arquitetura 32/64 bits.
-   Versão do Python e do Qt usada no build.
-   Versão do instalador.
-   Instalação limpa, inicialização e desinstalação.
-   Banco de dados e migrações.
-   Impressora, conexão e driver testados.
-   Backup e restauração.
-   Problemas conhecidos e data do último teste.

Não marcar uma plataforma como suportada apenas porque o código compila.

------------------------------------------------------------------------

## 10. GitHub e fluxo de contribuição

-   Manter branches curtas e pull requests revisáveis.
-   Usar tags semânticas de versão: `MAJOR.MINOR.PATCH`.
-   Abrir issues para bugs, melhorias e compatibilidade.
-   Não aceitar mudanças de banco sem migração e testes.
-   Usar CI para formatar, analisar e testar código.
-   Não incluir arquivos `.db` reais, backups, instaladores locais
    temporários, credenciais ou configurações privadas.
-   Adicionar um `SECURITY.md` com instruções de reporte responsável de
    vulnerabilidades.
-   Manter changelog e notas de release.
-   Separar claramente bugs de Windows 7 de bugs do Linux, incluindo
    logs sanitizados e informações da versão.
-   Documentar que contribuições precisam respeitar a licença do projeto
    e as licenças de terceiros.

------------------------------------------------------------------------

## 11. Checklist de release

Antes de publicar qualquer versão:

-   [ ] Testes unitários e de integração aprovados.
-   [ ] Testes de permissões e operações críticas aprovados.
-   [ ] Migração testada a partir da versão anterior.
-   [ ] Backup e restauração validados.
-   [ ] Build instalado em Windows 7 de teste, se esse alvo estiver
    incluído no release.
-   [ ] Pacote `.deb` instalado na versão mínima Linux suportada.
-   [ ] Leitor de código de barras e impressão testados nos modelos
    declarados.
-   [ ] Verificação de licenças de dependências concluída.
-   [ ] Checksums dos artefatos gerados.
-   [ ] Changelog e limitações conhecidas atualizados.
-   [ ] Nenhum dado real ou segredo incluído nos artefatos.
-   [ ] Instruções de instalação e recuperação publicadas.

------------------------------------------------------------------------

## 12. Resumo das decisões

1.  **Compatibilidade com Windows 7 e Linux baseado em Debian é
    prioridade de projeto**, validada por protótipo e testes reais.
2.  **PySide6/Qt 6 não é a escolha para o alvo Windows 7.** A hipótese
    inicial é PyQt5/Qt 5 com versões fixadas, sujeita a prova de
    compatibilidade.
3.  **Python 3.8 é legado e está sem suporte.** Usá-lo para o alvo
    Windows 7 envolve risco documentado; não o apresentar como escolha
    moderna e segura.
4.  **Uma base de código, builds separados:** compartilhar domínio e
    casos de uso, isolar integrações de sistema operacional.
5.  **SQLite offline-first**, transações consistentes, migrações
    versionadas e dinheiro em centavos.
6.  **Segurança, auditoria e backup desde a primeira fase.** Hash
    encadeado detecta alguns tipos de alteração, mas não impede
    adulteração por quem controla a máquina.
7.  **Empacotamento desde a Fase 0:** instalador `.exe` e pacote `.deb`
    testados em instalações limpas.
8.  **O sistema básico não é fiscal** até que exista módulo específico
    validado.
9.  **Projeto open source com suporte como serviço:** instalação,
    treinamento, customizações e integrações podem financiar a
    manutenção.
10. **O Windows 7 deve ser tratado como plataforma legada.** A
    compatibilidade deve ser honesta, limitada às combinações
    efetivamente testadas e acompanhada de recomendações de mitigação.

## Próximo passo recomendado

Implementar apenas o protótipo da Fase 0. Antes de construir o ERP
completo, provar que a interface PyQt5/Qt 5, o banco SQLite, o
empacotamento e as operações básicas funcionam nos sistemas-alvo. Se a
cadeia Windows 7 não for viável com as dependências selecionadas,
avaliar Tkinter ou outra abordagem antes de acumular código dependente
da stack.
