"""Testes arquiteturais (RNF-01): fronteiras de dependência verificadas por AST."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "matraca"

#: pacote de terceiros -> únicos arquivos (relativos a `matraca/`) autorizados a importá-lo
THIRD_PARTY_OWNERS: dict[str, tuple[str, ...]] = {
    "fitz": ("pdf/pymupdf_reader.py",),
    "pymupdf": ("pdf/pymupdf_reader.py",),
    "edge_tts": ("audio/edge_tts_client.py",),
    "customtkinter": ("gui/desktop_app.py",),
    "tkinter": ("gui/desktop_app.py", "doctor.py"),
    "streamlit": ("web/streamlit_app.py", "web/page_logic.py", "doctor.py"),
    "mutagen": ("audio/mp3_writer.py", "audio/mp3_validation.py"),
}


def _imports(path: Path) -> set[str]:
    """Módulos importados (nome completo) por um arquivo, incluindo imports dentro de funções."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def _py_files(sub: str) -> list[Path]:
    return sorted((PKG / sub).rglob("*.py"))


def test_core_so_importa_stdlib_e_matraca_interno() -> None:
    permitidos_matraca = (
        "matraca.core",
        "matraca.config",
        "matraca.text",
        "matraca.audio.chunking",
    )
    stdlib = sys.stdlib_module_names
    for arquivo in _py_files("core"):
        for modulo in _imports(arquivo):
            raiz = modulo.split(".")[0]
            if raiz == "matraca":
                assert modulo.startswith(permitidos_matraca) or modulo == "matraca", (
                    f"{arquivo.name} importa {modulo}"
                )
            else:
                assert raiz in stdlib, f"{arquivo.name} importa terceiro: {modulo}"


def test_terceiros_restritos_aos_adaptadores() -> None:
    for arquivo in PKG.rglob("*.py"):
        rel = arquivo.relative_to(PKG).as_posix()
        for modulo in _imports(arquivo):
            raiz = modulo.split(".")[0]
            if raiz in THIRD_PARTY_OWNERS:
                assert rel in THIRD_PARTY_OWNERS[raiz], f"{rel} não pode importar {modulo}"


@pytest.mark.parametrize("sub", ["text", "extractors", "core"])
def test_camadas_internas_nao_importam_interfaces(sub: str) -> None:
    for arquivo in _py_files(sub):
        for modulo in _imports(arquivo):
            assert not modulo.startswith(("matraca.gui", "matraca.web")), (
                f"{arquivo.name} importa interface: {modulo}"
            )


def test_import_matraca_sem_efeitos_colaterais() -> None:
    codigo = (
        "import sys, logging; import matraca;"
        "assert not logging.getLogger('matraca').handlers;"
        "pesados=[m for m in ('fitz','edge_tts','streamlit','customtkinter') if m in sys.modules];"
        "assert not pesados, pesados"
    )
    resultado = subprocess.run(  # noqa: S603 - argumentos fixos, sem entrada do usuário
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=False
    )
    assert resultado.returncode == 0, resultado.stderr


def test_sem_eval_exec_ou_shell_true() -> None:
    for arquivo in PKG.rglob("*.py"):
        tree = ast.parse(arquivo.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id not in {"eval", "exec"}, f"{arquivo.name}: {func.id}"
                for kw in node.keywords:
                    if kw.arg == "shell":
                        assert not (isinstance(kw.value, ast.Constant) and kw.value.value is True)
