# Instruções de Teste em VM Limpa — NexoERP

## Objetivo
Validar que o build PyInstaller `onedir` funciona corretamente em **VMs limpas** (sem Python, sem dependências de desenvolvimento), tanto no **Windows 10+** quanto no **Linux (Debian/Ubuntu)**.

---

## 📦 O que testar

| Cenário | Windows | Linux |
|---------|---------|-------|
| Instalação limpa (Inno Setup / .deb / AppImage) | ✅ | ✅ |
| Primeira execução (bootstrap + migrações) | ✅ | ✅ |
| Login (tela gráfica) | ✅ | ✅ |
| Operações básicas (CRUD empresa, produto, venda) | ✅ | ✅ |
| Backup / Restore | ✅ | ✅ |
| Atualização por cima (preservação de dados) | ✅ | ✅ |
| Desinstalação (dados preservados) | ✅ | ✅ |
| Impressão (spooler / CUPS) | ✅ | ✅ |
| Wayland / X11 (sem artefato branco) | — | ✅ |

---

## 🖥️ Preparação das VMs

### Windows 10/11 (VM limpa)
- **ISO**: Windows 10/11 Pro (PT-BR), sem updates opcionais
- **Recursos**: 2 vCPU, 4 GB RAM, 60 GB disco
- **Rede**: NAT (acesso internet para download se necessário)
- **NÃO instalar**: Python, Visual Studio, Qt, drivers de impressora (opcional)
- **Snapshot**: Faça snapshot **antes** de qualquer teste ("Clean State")

### Linux (Debian 12 / Ubuntu 22.04 / Mint 21) (VM limpa)
- **ISO**: Instalação mínima (server/minimal), PT-BR
- **Recursos**: 2 vCPU, 4 GB RAM, 40 GB disco
- **Desktop**: GNOME (Wayland padrão) + X11 opcional
- **Pacotes base**: `sudo apt update && sudo apt install -y cups cups-client`
- **NÃO instalar**: Python 3.12+ (o bundle traz o runtime), PySide6, desenvolvimento
- **Snapshot**: Faça snapshot **antes** de qualquer teste ("Clean State")

---

## 📥 Obtendo os Artefatos

### Opção 1: Build local (se você buildou)
```bash
# Linux
/home/carlos/Documentos/NexoERP/dist/ERP/ERP

# Windows
C:\path\NexoERP\dist\ERP\ERP.exe
```

### Opção 2: Baixar do GitHub Releases (quando houver release publicada)
```bash
# Linux AppImage
wget https://github.com/ivanmamedio/NexoERP/releases/download/vX.Y.Z/nexoerp-X.Y.Z-x86_64.AppImage
chmod +x nexoerp-*.AppImage

# Linux .deb
wget https://github.com/ivanmamedio/NexoERP/releases/download/vX.Y.Z/nexoerp-X.Y.Z-amd64.deb
sudo dpkg -i nexoerp-*.deb

# Windows Installer
# Baixe NexoERP-Setup.exe e execute
```

---

## 🧪 Roteiro de Testes (Execute na ORDEM)

### Teste 1 — Smoke Test Automatizado (Headless)
> Valida bootstrap, migrações, login (sem UI), CRUD, backup, preservação de dados.

**Linux:**
```bash
cd /home/carlos/Documentos/NexoERP
# Se usando build local:
./dist/ERP/ERP --smoke-test

# Se usando AppImage:
./nexoerp-*.AppImage --smoke-test

# Se instalado via .deb:
nexorp --smoke-test
```

**Windows (PowerShell):**
```powershell
cd C:\path\NexoERP
# Se usando build local:
.\dist\ERP\ERP.exe --smoke-test

# Se instalado:
& "C:\Program Files\NexoERP\ERP.exe" --smoke-test
```

**Esperado:** Exit code 0, log em `smoke_test.log`, relatório em `smoke_test_report.json`.

---

### Teste 2 — Primeira Execução Gráfica (GUI)
> Abre a tela de splash → login → janela principal.

**Linux (Wayland - padrão):**
```bash
./dist/ERP/ERP
# ou
./nexoerp-*.AppImage
```

**Linux (X11 - para comparar):**
```bash
QT_QPA_PLATFORM=xcb ./dist/ERP/ERP
```

**Windows:**
```powershell
.\dist\ERP\ERP.exe
```

**Checklist visual:**
- [ ] Splash screen aparece com logo
- [ ] Tela de login abre **sem quadrado branco** (artefato Wayland)
- [ ] Fundo do login é cinza claro (`#f4f6f8`), card branco com sombra
- [ ] Campos: "Número do usuário" + "Senha" + botão "Entrar"
- [ ] Login funciona (use credenciais criadas no primeiro uso ou `NEXOERP_ADMIN_PASSWORD`)
- [ ] Janela principal abre com menus laterais
- [ ] Troca de empresa na barra de status funciona

---

### Teste 3 — Operações Básicas (CRUD)
Na janela principal:
1. **Empresas** → Nova Empresa → Preencha → Salvar
2. **Catálogo** → Novo Produto → SKU, nome, categoria, preço, custo → Salvar
3. **Caixa** → Abrir Sessão → Valor abertura → Confirmar
4. **PDV** (F2/F4/F6/F8) → Adicionar item → Pagamento misto → Finalizar
5. **Tesouraria** → Abas: Fluxo, Pagar, Receber, Alertas, Categorias
6. **Relatórios** → Gerar CSV/PDF
7. **Configurações** → Header/footer cupom, timeout

---

### Teste 4 — Backup e Restore
1. Menu **Backup** → Criar backup manual
2. Verifique se arquivo `.zip` aparece em `~/NexoERP/backups/` (Linux) ou `%APPDATA%\NexoERP\backups\` (Windows)
3. **Restore**: selecione backup → Restaurar → Confirme
4. Verifique se dados voltaram ao estado do backup

---

### Teste 5 — "Atualização" (Preservação de Dados)
1. Feche o app
2. **Simule atualização**: substitua o executável/extrai novo AppImage/instala novo .deb/rode novo Inno Setup
3. Abra o app novamente
4. Verifique: empresas, produtos, vendas, caixa → **devem estar lá**

---

### Teste 6 — Desinstalação
**Linux (.deb):**
```bash
sudo apt remove nexoerp
# Verifique: ~/NexoERP/ (dados) NÃO foi apagado
```

**Windows (Inno Setup):**
- Painel de Controle → Desinstalar NexoERP
- Verifique: `%APPDATA%\NexoERP\` (dados) NÃO foi apagado

---

### Teste 7 — Impressão (se houver hardware)
| Plataforma | Teste |
|------------|-------|
| Windows | Impressora térmica USB → spooler RAW → ESC/POS |
| Linux | Impressora térmica USB → CUPS → ESC/POS |
| Ambos | Preview na tela (sempre funciona) |

---

### Teste 8 — Wayland vs X11 (Linux only)
Execute **duas vezes**:
```bash
# Wayland (padrão no GNOME, KDE Plasma 6+)
./dist/ERP/ERP

# X11 (forçado)
QT_QPA_PLATFORM=xcb ./dist/ERP/ERP
```

**Compare:**
- [ ] Login abre sem artefato em **ambos**
- [ ] Sombra do card visível em ambos
- [ ] Fonte, cores, espaçamento iguais
- [ ] Janela principal redimensionável em ambos

---

## 📋 Checklist de Resultado (Preencha e me envie)

### VM Windows 10/11
| Item | Status | Observações |
|------|--------|-------------|
| Instalação Inno Setup | ☐ OK / ☐ FALHA | |
| Primeira execução (bootstrap) | ☐ OK / ☐ FALHA | |
| Splash + Login (sem artefato) | ☐ OK / ☐ FALHA | |
| CRUD básico | ☐ OK / ☐ FALHA | |
| Backup / Restore | ☐ OK / ☐ FALHA | |
| Atualização preserva dados | ☐ OK / ☐ FALHA | |
| Desinstalação preserva dados | ☐ OK / ☐ FALHA | |
| Impressão (se testou) | ☐ OK / ☐ FALHA / ☐ N/A | |

### VM Linux (Debian/Ubuntu/Mint)
| Item | Status | Observações |
|------|--------|-------------|
| Instalação .deb | ☐ OK / ☐ FALHA | |
| Instalação AppImage | ☐ OK / ☐ FALHA | |
| Primeira execução (bootstrap) | ☐ OK / ☐ FALHA | |
| Splash + Login **Wayland** (sem artefato) | ☐ OK / ☐ FALHA | |
| Splash + Login **X11** (sem artefato) | ☐ OK / ☐ FALHA | |
| CRUD básico | ☐ OK / ☐ FALHA | |
| Backup / Restore | ☐ OK / ☐ FALHA | |
| Atualização preserva dados | ☐ OK / ☐ FALHA | |
| Desinstalação preserva dados | ☐ OK / ☐ FALHA | |
| Impressão CUPS (se testou) | ☐ OK / ☐ FALHA / ☐ N/A | |

---

## 📤 Como me enviar os resultados

1. **Logs**: Anexe `smoke_test.log` e `smoke_test_report.json` de cada VM
2. **Checklist**: Preencha as tabelas acima (pode ser no corpo do email/mensagem)
3. **Screenshots** (opcional mas ajuda):
   - Tela de login (Wayland e X11)
   - Janela principal
   - Qualquer erro/artefato
4. **Versão do SO**: `cat /etc/os-release` (Linux) / `winver` (Windows)
5. **Versão do Qt no bundle**: rode `ldd dist/ERP/ERP | grep Qt` (Linux) ou veja no About do instalador

---

## 🆘 Problemas Conhecidos / Workarounds

| Problema | Workaround |
|----------|------------|
| `libxcb-cursor.so.0` não encontrado (X11) | `sudo apt install libxcb-cursor0` |
| Fonte feia / pequena no Wayland | `QT_QPA_PLATFORM=wayland QT_FONT_DPI=96 ./ERP` |
| AppImage não executa (FUSE) | `./nexoerp-*.AppImage --appimage-extract && ./squashfs-root/AppRun` |
| Windows: "Windows protegeu seu PC" | "Mais informações" → "Executar mesmo assim" (assinatura digital pendente) |
| Linux: erro de permissão em `/usr/bin` (AppImage) | Use `~/Applications` ou instale via `.deb` |

---

## 📞 Próximos Passos Após Teste

1. Se **tudo OK** → Partimos para **Opção B: Teste Visual Wayland dedicado** (já coberto acima) → **Fase 5**
2. Se **falhas** → Me passe os logs → Eu corrijo → Rebuild → Testamos novamente
3. **Não avance** para Fase 5 sem builds validados em VMs limpas

---

**Dúvidas?** Me avise. O script `smoke_test_vm.py` já está no repo em `scripts/`.