# Correções para o NexoERP — instruções para o Claude

## Objetivo

Corrigir os problemas de carregamento da logo no modo de desenvolvimento e no executável PyInstaller `onedir`, e remover os artefatos visuais da tela de login no Fedora/Wayland. A implementação deve continuar compatível com a arquitetura atual do projeto e preservar o fluxo de autenticação existente.

**Importante:** o arquivo `correção.md` recebido contém grandes blocos repetidos e trechos de Python/QSS malformados (por exemplo, pontos finais no lugar de `;`, layouts e widgets recriados várias vezes e aspas/parênteses ausentes). Não copie esse conteúdo literalmente. Use este documento como especificação e confira os arquivos reais do repositório antes de editar.

## Regras de execução

1. Inspecione primeiro `src/erp/modules/identity/presentation/login_view.py`, `src/erp/__main__.py`, `packaging/pyinstaller.spec`, a localização real de `logo.png`, os testes existentes e o comando de build documentado no projeto.
2. Faça alterações pequenas e coerentes; não reescreva módulos não relacionados.
3. Preserve as interfaces públicas usadas pelo restante do projeto, especialmente `LoginDialog`, `set_presenter`, `show_error` e `clear_password`, além do contrato real de `LoginPresenter`.
4. Não altere a autenticação, os papéis/permissões, o banco de dados ou credenciais neste trabalho.
5. Não alegue que o problema foi corrigido sem executar verificações. Se alguma verificação não puder ser executada, informe exatamente qual e por quê.
6. Antes de editar, mostre um resumo dos arquivos que pretende alterar. Depois, apresente o diff e os resultados dos testes em **português**.
7. Não faça commit, push, exclusão de arquivos nem limpeza ampla de diretórios sem autorização explícita.
8. Nunca remova diretórios de dados do usuário ou bancos de dados. Para o build, limpe apenas diretórios gerados que tenham sido confirmados como artefatos do PyInstaller.

---

## Correção 1 — recurso compartilhado para encontrar a logo

Evite espalhar lógica diferente de caminhos em cada janela. Implemente ou reutilize um helper de recursos, por exemplo `src/erp/ui/resource_paths.py`, desde que isso se encaixe na estrutura existente.

Requisitos para localizar a logo:

- Desenvolvimento: `src/erp/ui/resources/logo.png`.
- Aplicação empacotada: caminho de dados relativo a `sys._MEIPASS` quando essa variável existir.
- Não dependa do diretório atual de execução (`Path.cwd()`).
- Valide que o arquivo existe e que `QPixmap` não é nulo.
- Se a logo não estiver disponível, a aplicação deve continuar abrindo; registre um aviso útil, sem crash.
- Não use caminhos absolutos específicos da máquina, como `/home/carlosivan/...`.

Implementação de referência:

```python
from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Retorna um caminho de recurso em desenvolvimento ou no bundle PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        # Este arquivo fica em src/erp/ui/resource_paths.py.
        # parents[0] = ui; parents[1] = erp; parents[2] = src.
        base = Path(__file__).resolve().parents[2]

    return base.joinpath(*parts)
```

Com esse helper, o caminho da logo é:

```python
logo_path = resource_path("erp", "ui", "resources", "logo.png")
```

Atenção: o exemplo acima usa `base=src` em desenvolvimento e `_MEIPASS` no bundle, então o mesmo caminho relativo funciona nos dois cenários. Se já existir um helper equivalente no projeto, prefira reutilizá-lo e não crie duplicação.

---

## Correção 2 — `packaging/pyinstaller.spec`

Ajuste o `.spec` existente sem remover dados necessários ao Alembic nem imports dinâmicos já exigidos pelo projeto.

Verifique antes:
- se `src/erp/ui/resources/logo.png` realmente existe;
- se o destino do recurso corresponde ao caminho esperado pelo helper (`erp/ui/resources/logo.png`);
- se o arquivo de ícone do executável existe no caminho indicado pelo `.spec`;
- se o projeto usa `onedir` (o spec fornecido usa `EXE(..., exclude_binaries=True)` e `COLLECT`).

O trecho de `datas` deve conter entradas equivalentes a estas:

```python
datas = [
    (
        os.path.join(DB_DIR, "alembic"),
        "erp/shared/infrastructure/database/alembic",
    ),
    (LOGO_PATH, "erp/ui/resources"),
]
```

Não declare uma segunda variável `datas` se o spec já usa a lista diretamente em `Analysis`; adapte o código existente. Confirme que `LOGO_PATH` é validado antes de iniciar o build, com uma mensagem clara caso esteja ausente. Não invente uma localização alternativa da logo.

Não faça alterações desnecessárias em `hiddenimports`, `excludes`, UPX ou configurações de plataforma sem evidência de que são necessárias. Caso o `.spec` seja executado em Linux e o arquivo `icon.ico` não exista, trate isso de forma explícita e compatível com a estratégia de empacotamento do projeto, sem mascarar outros erros.

---

## Correção 3 — reconstruir `login_view.py` sem duplicação nem transparência

O arquivo atual apresentado no material tem blocos de criação de campos, botões e layouts repetidos muitas vezes. Substitua a implementação duplicada por uma única construção de interface, mas confira primeiro os métodos e o contrato do presenter existentes no repositório.

Requisitos visuais:
- Usar `QDialog` com decoração normal do sistema operacional.
- **Não** definir `Qt.FramelessWindowHint`.
- **Não** habilitar `Qt.WA_TranslucentBackground`.
- Fundo opaco; não depender de transparência para desenhar o card.
- Um único `QGraphicsDropShadowEffect`, aplicado ao card.
- Reservar margens ao redor do card para a sombra não ser cortada.
- Um único `QVBoxLayout` para o card e um único layout principal para o diálogo.
- Criar cada campo, label e botão apenas uma vez.
- Manter a senha mascarada.
- Enter deve continuar submetendo o formulário se esse for o comportamento atual.
- Manter as mensagens de erro e a chamada do presenter.
- Não colocar regra de autenticação na view.
- Não deixar o erro invisível se o login falhar.

### Implementação-base sugerida

Use esta implementação como base e adapte os detalhes de acordo com o contrato real do repositório. Não substitua silenciosamente APIs ou comportamentos que os testes atuais esperam.

```python
"""Tela de login Qt; a autenticação é delegada ao presenter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from erp.ui.resource_paths import resource_path

if TYPE_CHECKING:
    from erp.modules.identity.presentation.login_presenter import LoginPresenter

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """Janela modal de login com decoração nativa e fundo opaco."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setFixedSize(480, 560)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6f8;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(28, 28, 28, 28)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QWidget(self)
        self._card.setObjectName("loginCard")
        self._card.setStyleSheet("""
            QWidget#loginCard {
                background-color: #ffffff;
                border: 1px solid #e1e5e8;
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 4)
        self._card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        self._logo_label = QLabel(self._card)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(72)
        self._load_logo()
        card_layout.addWidget(self._logo_label)

        title = QLabel("NexoERP", self._card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600; color: #2c3e50; border: none;")
        card_layout.addWidget(title)

        subtitle = QLabel("Sistema de Gestão Comercial", self._card)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #7f8c8d; border: none;")
        card_layout.addWidget(subtitle)

        self._username = QLineEdit(self._card)
        self._username.setObjectName("usernameInput")
        self._username.setPlaceholderText("Usuário")
        self._username.setMinimumHeight(40)

        self._password = QLineEdit(self._card)
        self._password.setObjectName("passwordInput")
        self._password.setPlaceholderText("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setMinimumHeight(40)

        field_style = """
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """
        self._username.setStyleSheet(field_style)
        self._password.setStyleSheet(field_style)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(14)
        form.addRow("Usuário:", self._username)
        form.addRow("Senha:", self._password)
        card_layout.addLayout(form)

        self._error_label = QLabel(self._card)
        self._error_label.setWordWrap(True)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet("color: #c0392b; font-size: 12px; border: none;")
        self._error_label.hide()
        card_layout.addWidget(self._error_label)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self._card)
        submit_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if submit_button is not None:
            submit_button.setText("Entrar")
            submit_button.setMinimumHeight(40)
            submit_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 9px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 120px;
                }
                QPushButton:hover { background-color: #2980b9; }
                QPushButton:pressed { background-color: #1f618d; }
            """)

        self._buttons.accepted.connect(self._on_submit)
        card_layout.addWidget(self._buttons, alignment=Qt.AlignmentFlag.AlignCenter)

        outer_layout.addWidget(self._card)

    def _load_logo(self) -> None:
        """Carrega a logo em desenvolvimento ou no bundle PyInstaller."""
        path = resource_path("erp", "ui", "resources", "logo.png")
        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            logger.warning("Não foi possível carregar a logo do NexoERP: %s", path)
            self._logo_label.setText("NexoERP")
            return

        self._logo_label.setPixmap(
            pixmap.scaled(
                160,
                72,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def set_presenter(self, presenter: LoginPresenter) -> None:
        self._presenter = presenter

    def show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def clear_password(self) -> None:
        self._password.clear()
        self._password.setFocus()

    def _on_submit(self) -> None:
        if self._presenter is None:
            logger.error("Tentativa de login sem LoginPresenter configurado.")
            self.show_error("O login não está disponível no momento.")
            return

        self._error_label.hide()
        self._presenter.login(
            self._username.text(),
            self._password.text(),
        )
```

### Observações obrigatórias sobre a implementação-base

- O import `from erp.ui.resource_paths import resource_path` só será válido se o helper for criado nesse local e esse pacote estiver incluído no projeto. Se a organização real for diferente, ajuste o import corretamente.
- Confira se o presenter espera `login(username, password)` e se os testes dependem de `parent: object | None`; preserve a assinatura compatível com a base de código.
- `WA_TranslucentBackground=False` explicita que a janela não deve ser transparente; não adicione flags de janela sem necessidade.
- A sombra pode variar entre compositores. Se houver artefato persistente, teste primeiro sem `QGraphicsDropShadowEffect` para isolar a causa. Não reintroduza frameless/translucent como solução.
- A implementação acima é uma base de correção, não uma alegação de que foi validada no ambiente do usuário.

---

## Correção 4 — splash screen em `src/erp/__main__.py`

Inspecione o código real antes de mudar. Se o splash já existe e funciona, não o reescreva; ajuste apenas a origem da logo para usar o helper de recursos compartilhado.

Requisitos:
1. Use o mesmo `resource_path("erp", "ui", "resources", "logo.png")` ou equivalente compatível com o projeto.
2. Verifique `QPixmap.isNull()` antes de atribuir a imagem.
3. Se a imagem falhar, permita que a inicialização continue sem splash com logo; registre aviso útil.
4. Não crie duas telas de splash nem altere a sequência de inicialização.
5. Não altere autenticação, migrações ou inicialização do banco como parte desta correção.

---

## Correção 5 — testes e validação

Adicione ou adapte testes com as ferramentas já usadas pelo projeto. Evite exigir uma sessão gráfica real nos testes unitários; use o mecanismo Qt já adotado nos testes existentes.

### Verificações mínimas

1. **Sintaxe/imports:** os módulos alterados importam sem erro.
2. **Teste da view:** `LoginDialog` é criado, contém os campos esperados, mantém a senha mascarada e não possui `FramelessWindowHint`.
3. **Fluxo do presenter:** ao submeter, a view chama `presenter.login` com usuário e senha; quando não há presenter, a view não quebra.
4. **Logo ausente/inválida:** o diálogo continua sendo criado e exibe fallback sem crash.
5. **Recurso:** o helper resolve o arquivo real no ambiente de desenvolvimento; teste o caminho empacotado por inspeção do bundle/build.
6. **Regressão:** execute os testes relevantes de identidade/login e, depois, a suíte de testes que o projeto suporta.
7. **Build:** execute o comando de build documentado pelo projeto, usando o ambiente e as dependências instaladas. Não presuma que o build terminou corretamente só porque o comando foi iniciado.
8. **Execução gráfica:** teste a aplicação no Fedora/Wayland com a sessão normal. Se necessário, faça um teste separado com `QT_QPA_PLATFORM=xcb`, deixando claro que XCB é um diagnóstico alternativo, não uma prova de que Wayland foi corrigido.

### Exemplo de sequência de comandos

Primeiro confirme o diretório raiz do repositório e o ambiente de desenvolvimento. Adapte os comandos se o projeto não usar `uv`.

```bash
git status --short
uv run pytest tests/ -v
uv run pyinstaller packaging/pyinstaller.spec --clean --noconfirm
```

Não apague `dist/`, `build/` ou caches globais automaticamente. Se precisar reconstruir do zero, identifique primeiro os diretórios gerados pelo projeto e remova somente os artefatos específicos dessa build. Não use `sudo` para executar o build.

Após a compilação `onedir`, confirme que existe um arquivo equivalente a:

```text
dist/ERP/ERP
dist/ERP/_internal/erp/ui/resources/logo.png
```

**Atenção:** o caminho interno exato depende da versão/configuração do PyInstaller. Não declare falha apenas porque o arquivo está em outro subdiretório; verifique o conteúdo real do bundle e se ele corresponde ao caminho usado pela aplicação.

---

## Critérios de aceite

- [ ] `login_view.py` não tem blocos repetidos nem widgets/layouts recriados.
- [ ] A janela tem bordas e decoração nativas.
- [ ] Não há uso de `FramelessWindowHint` nem fundo translúcido na tela de login.
- [ ] Não há artefato branco no teste real do ambiente alvo; se persistir, registrar o resultado e isolar sombra/estilo em teste separado.
- [ ] A logo carrega em desenvolvimento.
- [ ] A logo está incluída no bundle e carrega no executável `onedir`.
- [ ] O splash screen usa o caminho de recurso correto e falha de forma segura.
- [ ] O fluxo de autenticação e o contrato da view permanecem compatíveis.
- [ ] Os testes relevantes foram executados e os resultados reais foram reportados.
- [ ] O diff não inclui alterações não relacionadas.

## Formato da resposta final do Claude

Responda em português, contendo:
1. Causa raiz confirmada de cada problema (ou diga se ainda não foi confirmada).
2. Arquivos modificados e resumo de cada alteração.
3. Testes/comandos executados com resultado real.
4. Resultado do build e localização verificada da logo no bundle.
5. Qualquer limitação ou teste que dependa de validação manual no Fedora/Wayland.
6. Diff/resumo das mudanças e riscos remanescentes.

Não diga “corrigido definitivamente” sem evidência reproduzível.
