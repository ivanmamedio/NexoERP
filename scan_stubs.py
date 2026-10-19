"""Lista arquivos .py vazios/triviais rastreados pelo git e camadas sem codigo real.

Uso (na raiz do repositorio): uv run python scan_stubs.py
Somente leitura: nao altera nenhum arquivo.
"""
from __future__ import annotations

import ast
import subprocess
from collections import defaultdict
from pathlib import Path

TEXT_EXT = {
    ".py", ".toml", ".ini", ".cfg", ".spec", ".iss",
    ".yml", ".yaml", ".md", ".importlinter", ".txt",
}


def tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    return [Path(p) for p in out.splitlines() if p]


def classify(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return "vazio"
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "real"
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # docstring ou Ellipsis
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
            and isinstance(node.value, (ast.List, ast.Tuple))
            and not node.value.elts
        ):
            continue
        return "real"
    return "trivial"


def dotted(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def main() -> None:
    files = tracked()
    py = [f for f in files if f.suffix == ".py" and f.parts[0] == "src"]
    texts = {
        f: f.read_text(encoding="utf-8", errors="ignore")
        for f in files
        if f.suffix in TEXT_EXT or f.name == ".importlinter"
    }

    kind = {f: classify(f) for f in py}

    print("== 1) Arquivos NAO __init__ vazios/triviais (candidatos a remocao) ==")
    any_found = False
    for f, k in sorted(kind.items()):
        if f.name != "__init__.py" and k != "real":
            any_found = True
            name = dotted(f)
            refs = [str(o) for o, t in texts.items() if o != f and name in t]
            print(f"- {f}  [{k}]  referencias: {len(refs)}" + (f"  -> {refs[:3]}" if refs else ""))
    if not any_found:
        print("(nenhum)")

    print("\n== 2) Pacotes (pastas) sem NENHUM codigo real abaixo deles ==")
    pkgs: dict[Path, list[str]] = defaultdict(list)
    for f, k in kind.items():
        for parent in f.parents:
            if parent.parts and parent.parts[0] == "src" and parent != Path("src"):
                pkgs[parent].append(k)
    empty_pkgs = sorted(p for p, ks in pkgs.items() if all(k != "real" for k in ks))
    # mostra so o nivel mais alto de cada ramo vazio
    top: list[Path] = []
    for p in empty_pkgs:
        if not any(parent in empty_pkgs for parent in p.parents):
            top.append(p)
    for p in top:
        name = dotted(p / "__init__.py")
        refs = [str(o) for o, t in texts.items() if not str(o).startswith(str(p)) and name in t]
        print(f"- {p}  referencias externas: {len(refs)}" + (f"  -> {refs[:4]}" if refs else ""))
    if not top:
        print("(nenhum)")

    print("\n== 3) Camadas por modulo (qtd de arquivos com codigo real) ==")
    mods = Path("src/erp/modules")
    if mods.exists():
        for m in sorted(p for p in mods.iterdir() if p.is_dir() and p.name != "__pycache__"):
            row = []
            for layer in ("domain", "application", "infrastructure", "presentation"):
                n = sum(1 for f, k in kind.items() if m / layer in f.parents and k == "real")
                row.append(f"{layer}={n}")
            print(f"- {m.name:12s} " + "  ".join(row))


if __name__ == "__main__":
    main()
