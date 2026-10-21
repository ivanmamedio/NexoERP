# Correção da tela de login — NexoERP (versão 2)

Contexto: PySide6 + PyInstaller (onedir), Fedora 44 (Wayland, com XCB como alternativa).

## 1. O que estava errado

O `login_view.py` da versão anterior **nem compilava**. A IA entrou em loop e o arquivo ficou assim:

- O bloco "Campos / Botão / Layout do card / Layout do dialog" foi repetido **43 vezes**.
- Cerca de **160 linhas de CSS** terminam com `.` em vez de `;` (`min-width: 120px.`, `color: #2c3e50.`). Qt ignora essas regras, e o texto dos campos pode ficar invisível.
- Há `"""` abertos sem o `)` de fechamento e sobrou um `PYEOF` solto no fim (resto de um heredoc de shell).
- Mesmo que compilasse, `QVBoxLayout(self._card)` e `QVBoxLayout(self)` eram criados dezenas de vezes no mesmo widget. O Qt emite "Attempting to set QLayout on QWidget which already has a layout" e ignora os layouts novos.
- `QGraphicsDropShadowEffect` estava aplicado **no card inteiro**, que contém todos os campos. O efeito renderiza o card e os filhos em um buffer à parte, e isso é fonte conhecida de artefatos e texto estranho no Wayland. O diálogo também tinha margem 0, então a sombra seria cortada de qualquer jeito.
- O passo 3 (`__main__.py`) era só um `grep`, não uma correção.

Outros pontos que encontrei:

- **`admin/admin` funcionando contraria o CONTEXTO** ("não existe senha padrão"). Isso não é problema visual, mas precisa ser tratado (tarefa C.8 do Tasks.md).
- O spec usa `upx=True`. O UPX pode corromper bibliotecas do Qt, então está desligado abaixo.
- O logo só aparece no build se estiver em `datas`. Agora o spec falha com mensagem clara se o arquivo não existir.

> **Aviso:** não consegui rodar PySide6 neste ambiente (sem rede). O código abaixo passou apenas em checagem de sintaxe (`py_compile`). Rode o critério de pronto no seu projeto antes de confiar nele.

## 2. Solução

Estratégia: **janela normal** (com borda), sem Frameless nem Translucent. O card fica centralizado com a sombra feita por um `QFrame` vazio colocado atrás dele, na mesma célula de um `QGridLayout`. Como o frame da sombra não tem filhos, o efeito não toca nos campos.

### 2.1 `src/erp/shared/ui/resources.py` (arquivo novo)

```python
"""Resolve caminhos de recursos (imagens, ícones) em dev e no PyInstaller."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # .../src/erp


def resource_path(*parts: str) -> Path:
    """Retorna o caminho de um recurso dentro do pacote `erp`.

    Em build PyInstaller usa `sys._MEIPASS/erp`; em desenvolvimento, a pasta do pacote.
    """
    frozen_root = getattr(sys, "_MEIPASS", None)
    base = Path(frozen_root) / "erp" if frozen_root else _PACKAGE_ROOT
    return base.joinpath(*parts)
```

### 2.2 `src/erp/modules/identity/presentation/login_view.py` (substitui o arquivo inteiro)

```python
"""Tela de login (Qt). Não contém regra de negócio: delega ao presenter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from erp.shared.ui.resources import resource_path

if TYPE_CHECKING:
    from erp.modules.identity.presentation.login_presenter import LoginPresenter

logger = logging.getLogger(__name__)

_LOGO_WIDTH = 160
_SHADOW_MARGIN = 24
_CARD_MIN_WIDTH = 380

_QSS = """
QDialog { background-color: #f2f4f7; }
#loginShadow { background-color: #ffffff; border-radius: 12px; }
#loginCard { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; }
#loginTitle { font-size: 22px; font-weight: 600; color: #2c3e50; }
#loginSubtitle { font-size: 12px; color: #7f8c8d; margin-bottom: 12px; }
#loginError { font-size: 12px; color: #e74c3c; }
#loginCard QLineEdit {
    padding: 8px 12px;
    border: 1px solid #bdc3c7;
    border-radius: 6px;
    font-size: 14px;
    background-color: #ffffff;
    color: #2c3e50;
    selection-background-color: #3498db;
}
#loginCard QLineEdit:focus { border: 2px solid #3498db; }
#loginButton {
    background-color: #3498db;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
    min-width: 120px;
}
#loginButton:hover { background-color: #2980b9; }
#loginButton:pressed { background-color: #1a6fa0; }
"""


class LoginDialog(QDialog):
    """Diálogo modal de login: janela normal, card centralizado com sombra."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: LoginPresenter | None = None

        self.setWindowTitle("NexoERP — Entrar")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setStyleSheet(_QSS)

        self._logo_label = QLabel()
        self._logo_label.setObjectName("loginLogo")
        self._title_label = QLabel("NexoERP")
        self._title_label.setObjectName("loginTitle")
        self._subtitle_label = QLabel("Sistema de Gestão Comercial")
        self._subtitle_label.setObjectName("loginSubtitle")
        self._username = QLineEdit()
        self._username.setObjectName("loginUsername")
        self._username.setPlaceholderText("Usuário")
        self._username.setAccessibleName("Usuário")
        self._password = QLineEdit()
        self._password.setObjectName("loginPassword")
        self._password.setPlaceholderText("Senha")
        self._password.setAccessibleName("Senha")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._error_label = QLabel()
        self._error_label.setObjectName("loginError")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        self._button = QPushButton("Entrar")
        self._button.setObjectName("loginButton")
        self._button.setDefault(True)
        self._button.clicked.connect(self._on_submit)

        self._load_logo()

        self._card = self._build_card()
        self._shadow_host = self._build_shadow_host()

        # Os dois widgets ocupam a MESMA célula: a sombra fica atrás do card.
        layout = QGridLayout(self)
        layout.setContentsMargins(
            _SHADOW_MARGIN, _SHADOW_MARGIN, _SHADOW_MARGIN, _SHADOW_MARGIN
        )
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self._shadow_host, 0, 0)
        layout.addWidget(self._card, 0, 0)
        self._card.raise_()

    # --- construção ---------------------------------------------------------

    def _build_shadow_host(self) -> QFrame:
        """Frame vazio (sem filhos) que carrega a sombra, evitando artefatos."""
        host = QFrame(self)
        host.setObjectName("loginShadow")
        effect = QGraphicsDropShadowEffect(host)
        effect.setBlurRadius(24)
        effect.setOffset(0, 4)
        effect.setColor(QColor(0, 0, 0, 70))
        host.setGraphicsEffect(effect)
        return host

    def _build_card(self) -> QFrame:
        card = QFrame(self)
        card.setObjectName("loginCard")
        card.setMinimumWidth(_CARD_MIN_WIDTH)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)
        center = Qt.AlignmentFlag.AlignCenter
        layout.addWidget(self._logo_label, alignment=center)
        layout.addWidget(self._title_label, alignment=center)
        layout.addWidget(self._subtitle_label, alignment=center)
        layout.addWidget(self._username)
        layout.addWidget(self._password)
        layout.addWidget(self._error_label)
        layout.addWidget(self._button, alignment=center)
        return card

    def _load_logo(self) -> None:
        """Carrega o logo (dev e PyInstaller). Se faltar, esconde o rótulo sem quebrar."""
        path = resource_path("ui", "resources", "logo.png")
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logger.warning("Logo não encontrado ou inválido: %s", path)
            self._logo_label.hide()
            return
        ratio = self.devicePixelRatioF()
        scaled = pixmap.scaledToWidth(
            int(_LOGO_WIDTH * ratio), Qt.TransformationMode.SmoothTransformation
        )
        scaled.setDevicePixelRatio(ratio)
        self._logo_label.setPixmap(scaled)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # --- LoginView protocol -------------------------------------------------

    def set_presenter(self, presenter: LoginPresenter) -> None:
        self._presenter = presenter

    def show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def clear_password(self) -> None:
        self._password.clear()
        self._password.setFocus()

    # --- internals ----------------------------------------------------------

    def _on_submit(self) -> None:
        if self._presenter is None:
            return
        self._error_label.hide()
        self._presenter.login(self._username.text(), self._password.text())
```

Observações sobre o arquivo:

- O contrato com o presenter é o mesmo: `set_presenter`, `show_error`, `clear_password`. Só vi no arquivo antigo esses três métodos e o `_on_submit`. O fechamento do diálogo após o login continua com quem chama (`accept()`).
- Removi o `keyPressEvent` (só chamava o `super`) e os `# type: ignore`.
- `setDefault(True)` no botão faz o Enter funcionar nos campos de texto.

### 2.3 `packaging/pyinstaller.spec` (versão completa)

Mudanças em relação à anterior: o logo é verificado antes do build e `upx=False` nos dois lugares (`EXE` e `COLLECT`).

```python
# -*- mode: python ; coding: utf-8 -*-
# NexoERP PyInstaller spec — modo onedir

import os

from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
ROOT_DIR = os.path.dirname(SPEC_DIR)
SRC_DIR = os.path.join(ROOT_DIR, "src")
DB_DIR = os.path.join(SRC_DIR, "erp", "shared", "infrastructure", "database")
LOGO_PATH = os.path.join(SRC_DIR, "erp", "ui", "resources", "logo.png")

if not os.path.isfile(LOGO_PATH):
    raise SystemExit(f"Logo não encontrado: {LOGO_PATH}")

a = Analysis(
    [os.path.join(SRC_DIR, "erp", "__main__.py")],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[
        (
            os.path.join(DB_DIR, "alembic"),
            "erp/shared/infrastructure/database/alembic",
        ),
        (LOGO_PATH, "erp/ui/resources"),  # mesmo destino que resource_path() espera
    ],
    hiddenimports=collect_submodules("erp") + collect_submodules("sqlalchemy"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["sqlalchemy.ext.asyncio"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ERP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX pode corromper bibliotecas do Qt
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, "packaging", "windows", "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ERP",
)
```

### 2.4 Testes: `tests/ui/test_login_view.py` (arquivo novo)

O teste de `_MEIPASS` simulado cobre exatamente o bug do logo no PyInstaller.

```python
"""Testes da tela de login e do carregamento de recursos."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton
from pytestqt.qtbot import QtBot

from erp.modules.identity.presentation.login_presenter import LoginPresenter
from erp.modules.identity.presentation.login_view import LoginDialog
from erp.shared.ui.resources import resource_path


class _FakePresenter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def login(self, username: str, password: str) -> None:
        self.calls.append((username, password))


def test_resource_path_in_dev_finds_logo() -> None:
    assert resource_path("ui", "resources", "logo.png").is_file()


def test_resource_path_uses_meipass_when_frozen(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    expected = tmp_path / "erp" / "ui" / "resources" / "logo.png"
    assert resource_path("ui", "resources", "logo.png") == expected


def test_dialog_is_a_normal_window(qtbot: QtBot) -> None:
    dialog = LoginDialog()
    qtbot.addWidget(dialog)
    assert not bool(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert not dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_logo_is_loaded(qtbot: QtBot) -> None:
    dialog = LoginDialog()
    qtbot.addWidget(dialog)
    logo = dialog.findChild(QLabel, "loginLogo")
    assert logo is not None
    assert not logo.pixmap().isNull()


def test_submit_calls_presenter_with_credentials(qtbot: QtBot) -> None:
    dialog = LoginDialog()
    qtbot.addWidget(dialog)
    fake = _FakePresenter()
    dialog.set_presenter(cast("LoginPresenter", fake))

    username = dialog.findChild(QLineEdit, "loginUsername")
    password = dialog.findChild(QLineEdit, "loginPassword")
    button = dialog.findChild(QPushButton, "loginButton")
    assert username is not None
    assert password is not None
    assert button is not None

    username.setText("maria")
    password.setText("s3nha-forte")
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert fake.calls == [("maria", "s3nha-forte")]
```

Se o `tests/ui/test_login.py` existente já usa fakes de `AuthenticateOutput` com `company_id`, mantenha como está. A tarefa C.2 trata disso.

## 3. Aplicar e testar

```bash
cd /home/carlosivan/Documentos/NexoERP
git switch -c correcao-login   # ou a branch que você estiver usando

# 1. Substitua login_view.py, crie shared/ui/resources.py e atualize o spec

# 2. Qualidade e testes (sem janela de verdade)
QT_QPA_PLATFORM=offscreen uv run pytest tests/ui -q
uv run ruff check . && uv run ruff format --check . && uv run mypy

# 3. Rodar em desenvolvimento nas duas plataformas gráficas
QT_QPA_PLATFORM=wayland uv run python -m erp
QT_QPA_PLATFORM=xcb uv run python -m erp

# 4. Build limpo
rm -rf build/pyinstaller dist/fedora-test ~/.cache/pyinstaller
uv run pyinstaller packaging/pyinstaller.spec --clean --distpath dist/fedora-test --noconfirm

# 5. Confirme que o logo entrou no pacote (PyInstaller 6+ usa a pasta _internal)
ls dist/fedora-test/ERP/_internal/erp/ui/resources/logo.png

# 6. Teste o executável nas duas plataformas
QT_QPA_PLATFORM=wayland ./dist/fedora-test/ERP/ERP
QT_QPA_PLATFORM=xcb ./dist/fedora-test/ERP/ERP
```

`QT_AUTO_SCREEN_SCALE_FACTOR=1` não é necessário: no Qt 6 o escalonamento de HiDPI já é automático.

## 4. Se o quadrado branco continuar

Depois desta correção o login não tem mais Frameless, Translucent nem efeito em container. Se ainda aparecer um quadrado branco, o culpado provável é outra janela, quase certamente a **splash**, que por natureza é uma janela sem borda.

1. Compare `QT_QPA_PLATFORM=wayland` com `=xcb`. Se só aparece em uma, é problema de plataforma, não do seu layout.
2. Comente temporariamente as linhas da `QSplashScreen` no `__main__.py` e rode de novo. Se o quadrado sumir, o problema está na splash. Me mande o `__main__.py` e eu ajusto.
3. Rode com `QT_DEBUG_PLUGINS=1` e veja se o plugin `wayland` carrega ou se o Qt está caindo para `xcb`. Se faltar o plugin Wayland no pacote, o Qt usa XCB sem avisar.

## 5. Pendência de segurança (não é visual)

O login com `admin/admin` funcionando viola a regra "não existe senha padrão" do CONTEXTO. Isso entra como **C.8** no Tasks.md: investigar de onde vem essa senha, parar e esperar aprovação antes de mexer. Não corrija isso junto com o visual do login.

## 6. Checklist

- [ ] `resources.py` criado e `login_view.py` substituído (sem blocos repetidos)
- [ ] `pyinstaller.spec` com logo em `datas` e `upx=False`
- [ ] `ruff`, `mypy` e `pytest` passando, com saídas reais
- [ ] Logo aparece em dev e no build (`ls` do passo 5 confirma)
- [ ] Sem quadrado branco em Wayland e em XCB
- [ ] Texto visível nos campos de usuário e senha
- [ ] Enter nos campos faz o login
