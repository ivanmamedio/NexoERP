# Documentação do Usuário - NexoERP

## Instalação em 5 Minutos

### Windows (PowerShell)

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

### Linux (Ubuntu/Debian)

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

## Primeiro Uso

### 1. Login Inicial
- Na primeira execução, crie o usuário administrador definindo a variável de ambiente:
  - **Windows (PowerShell):**
    ```powershell
    $env:NEXOERP_ADMIN_PASSWORD = "SuaSenhaSegura123"
    $env:NEXOERP_ADMIN_USERNAME = "admin"
    uv run python -m erp
    ```
  - **Linux:**
    ```bash
    export NEXOERP_ADMIN_PASSWORD="SuaSenhaSegura123"
    export NEXOERP_ADMIN_USERNAME="admin"
    uv run python -m erp
    ```
- Ou chame programaticamente: `create_first_admin(session, hasher, "admin", "senha")`

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