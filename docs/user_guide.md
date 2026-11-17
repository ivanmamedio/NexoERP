# Documentação do Usuário - NexoERP

## Instalação Rápida (Usuário Final)

### Opção 1: Pacotes Prontos (Recomendado para Usuários Finais)

Baixe o instalador para seu sistema operacional na [página de Releases](https://github.com/ivanmamedio/NexoERP/releases):

| Sistema | Arquivo | Como Instalar |
|---------|---------|---------------|
| **Windows 10/11** | `NexoERP-Setup.exe` | Execute o `.exe` e siga o assistente |
| **Linux (Ubuntu/Debian)** | `nexoerp-<versao>-amd64.deb` | `sudo apt install ./nexoerp-*.deb` |
| **Linux (Qualquer distro)** | `nexoerp-<versao>-x86_64.AppImage` | `chmod +x nexoerp-*.AppImage && ./nexoerp-*.AppImage` |

**Vantagens:** Não precisa instalar Python, Git, nem compilar. Instalação em 1 clique.

---

### Opção 2: Desenvolvimento / Código Fonte (Desenvolvedores)

#### Windows (PowerShell)

```powershell
# 1. Instalar Python 3.12+ (se não tiver)
# Baixe de https://python.org/downloads

# 2. Clonar o repositório
git clone https://github.com/ivanmamedio/NexoERP.git
cd NexoERP

# 3. Instalar dependências com uv (mais rápido que pip)
# Se não tiver uv: pip install uv
uv sync --all-groups --dev

# 4. Executar
uv run python -m erp
```

#### Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependências do sistema
sudo apt update && sudo apt install -y python3.12 python3.12-venv git

# 2. Clonar e instalar
git clone https://github.com/ivanmamedio/NexoERP.git
cd NexoERP

# 3. Instalar uv e dependências
pip install uv
uv sync --all-groups --dev

# 4. Executar
uv run python -m erp
```

#### Verificar Instalação

```bash
# Deve mostrar a versão sem erros
uv run python -m erp --help

# Teste headless (sem interface gráfica)
DISPLAY="" uv run python -m erp
# Deve mostrar: "Bootstrap successful" e sair com código 0
```

## Primeiro Uso

### 1. Login Inicial

**Opção A: Tela de Primeiro Uso (Recomendado)**
Na primeira execução sem usuários cadastrados, o NexoERP abre automaticamente a **Tela de Primeiro Uso** onde você:
1. Define o nome do primeiro administrador
2. Define a senha (mínimo 8 caracteres, com letra e número)
3. Clica em "Criar Administrador"

**Opção B: Variáveis de Ambiente (Automação/Deploy)**
```powershell
# Windows (PowerShell)
$env:NEXOERP_ADMIN_PASSWORD = "SuaSenhaSegura123"
$env:NEXOERP_ADMIN_USERNAME = "admin"
uv run python -m erp
```

```bash
# Linux
export NEXOERP_ADMIN_PASSWORD="SuaSenhaSegura123"
export NEXOERP_ADMIN_USERNAME="admin"
uv run python -m erp
```

**Regras de Senha:**
- Mínimo 8 caracteres
- Máximo 72 caracteres (limite do bcrypt)
- Pelo menos 1 letra e 1 número

> **Importante:** Não existe senha padrão `admin/admin`. O primeiro admin **sempre** deve ser criado explicitamente.

### 2. Configurar Empresa
1. Login com o usuário admin
2. Menu **Empresas** → **Nova Empresa**
3. Preencha: Razão Social, Nome Fantasia, CNPJ, Endereço
4. Salve

### 3. Cadastrar Produtos
1. Menu **Catálogo** → **Produtos** → **Novo**
2. Preencha: SKU, Nome, Categoria, Preço de Custo, Margem %, Preço de Venda
3. Defina Estoque Mínimo para alertas
4. Salve

### 4. Abrir Caixa
1. Menu **Caixa** → **Abrir Caixa**
2. Informe valor de abertura
3. Confirme

### 5. Primeira Venda (PDV)
1. Menu **PDV** (ou tecla F1)
3. Digite código do produto ou use `3*CÓDIGO` para multiplicar
4. Pressione Enter para adicionar
5. Pressione F2 para finalizar
6. Escolha forma de pagamento (Dinheiro, PIX, Cartão, Misto)
7. Confirme

## Backup e Restauração

### Backup Automático
- **Diário:** 02:00 (mantém últimos 30)
- **Mensal:** Dia 1 às 03:00 (mantém últimos 12)
- **Antes de migrações:** Automático ao atualizar
- **Fechamento de caixa:** Automático
- **Primeiro uso do dia:** Automático

### Backup Manual
1. Menu **Configurações** → **Backup**
2. Clique em **"Testar Backup Agora"**
3. O arquivo será salvo em `~/.local/share/NexoERP/backups/`

### Restauração (Caso de Desastre)
1. Feche o NexoERP completamente
2. Menu **Configurações** → **Backup** → **Restaurar**
3. Selecione o arquivo de backup (.zip)
4. O sistema fará uma cópia do banco atual (`.pre_restore.bak`)
5. Confirme a restauração
6. Reinicie o NexoERP

### Destino Secundário (Opcional)
Configure a variável de ambiente para backup em nuvem/pendrive:
- **Windows:** `$env:NEXOERP_BACKUP_SECONDARY = "D:\Backups\NexoERP"`
- **Linux:** `export NEXOERP_BACKUP_SECONDARY="/mnt/backup/NexoERP"`

## Atualização

```bash
git pull origin main
uv sync --all-groups --dev
uv run python -m erp
# Migrações rodam automaticamente na inicialização
```

## Solução de Problemas

### "Banco de dados travado"
- Feche todas as instâncias do NexoERP
- Verifique se não há arquivo `.lock` na pasta de dados
- Reinicie o computador se necessário

### "Erro de migração"
- Faça backup manual antes
- Verifique logs em `~/.local/share/NexoERP/logs/`
- Execute: `uv run alembic -c alembic.ini upgrade head`

### "PDV não encontra produto"
- Verifique se o produto está **Ativo**
- Verifique se o estoque > 0
- Use busca por nome (parte do nome) ou SKU exato

### "Permissão negada"
- Verifique se o usuário tem o papel correto
- Menu **Usuários** → editar usuário → **Papéis**
- Admin tem acesso total; Operador só PDV e Caixa

## Relatório de Erros (Novo)

O NexoERP possui um **manipulador global de exceções** que captura erros inesperados:

1. **Dialog amigável** aparece automaticamente em caso de erro
2. **Botão "Copiar Relatório"** copia o traceback completo para a área de transferência
3. **Botão "Fechar"** fecha o dialog e o aplicativo com segurança
4. **Log completo** salvo em `~/.local/share/NexoERP/logs/erp.log`

**Como reportar um erro:**
1. Clique em **"Copiar Relatório"** no dialog de erro
2. Cole no GitHub Issues ou envie para o suporte
3. Inclua: o que estava fazendo, versão do app, SO

> **Dica:** O relatório copiado NÃO contém senhas nem dados sensíveis.

## Atalhos do PDV

| Tecla | Ação |
|-------|------|
| F1 | Abrir PDV |
| F2 | Finalizar venda |
| F3 | Cancelar item |
| F4 | Desconto (requer PIN supervisor) |
| F5 | Pagamento misto |
| F10 | Fechar PDV |
| `3*123` | Adicionar 3 unidades do produto 123 |
| Enter | Confirmar/Adicionar |
| Esc | Cancelar/Limpar |

## Estrutura de Pastas

```
~/.local/share/NexoERP/          # Linux
%APPDATA%\NexoERP\               # Windows
├── erp.db                       # Banco de dados principal
├── backups/                     # Backups automáticos
│   ├── backup_1_20240115_020000_erp.db.zip
│   └── ...
├── reports/                     # Relatórios gerados
└── logs/                        # Logs de auditoria e erros
```

## Suporte

- **Issues:** https://github.com/ivanmamedio/NexoERP/issues
- **Logs de erro:** Menu **Configurações** → **Logs** → **Erros**
- **Auditoria:** Menu **Auditoria** → ver ações de usuários

---

**Versão:** 0.1.0  
**Licença:** AGPL-3.0-only  
**Compatibilidade:** Windows 10+, Linux (Ubuntu 22.04+, Debian 12+)