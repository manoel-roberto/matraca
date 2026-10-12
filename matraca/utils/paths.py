"""Utilitários de caminhos: sanitização de nomes, colisões, temporários e validação de saída."""

from __future__ import annotations

import contextlib
import logging
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from collections.abc import Iterator
from pathlib import Path

from matraca.core.exceptions import ArquivoJaExisteError, SaidaInvalidaError
from matraca.core.models import CollisionPolicy

_log = logging.getLogger(__name__)

_RESERVED_WINDOWS = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')
_SEPARATORS = re.compile(r"[\\/]")
_EXT_OK = re.compile(r"^\.[A-Za-z0-9]{1,10}$")


def sanitize_filename(name: str, *, max_length: int = 120, default: str = "arquivo") -> str:
    """Devolve um nome de arquivo seguro (apenas basename).

    Remove separadores de diretório, `..`, caracteres de controle e reservados do Windows,
    nomes reservados (CON, NUL...) e limita o comprimento preservando a extensão.
    """
    base = _SEPARATORS.split(unicodedata.normalize("NFC", name))[-1]
    base = "".join(ch for ch in base if unicodedata.category(ch)[0] != "C")
    base = _INVALID_CHARS.sub("_", base)
    base = base.strip(" .")
    if not base:
        return default

    path = Path(base)
    ext = path.suffix if _EXT_OK.match(path.suffix) else ""
    stem = base[: len(base) - len(ext)] if ext else base
    stem = stem.strip(" .")
    if not stem:
        stem = default
    if stem.upper() in _RESERVED_WINDOWS:
        stem = f"_{stem}"
    stem = stem[: max(1, max_length - len(ext))].rstrip(" .") or default
    return stem + ext


def resolve_collision(path: Path, policy: CollisionPolicy) -> Path:
    """Aplica a política de colisão de nomes.

    - `RENAME`: acrescenta sufixo ` (1)`, ` (2)`...
    - `OVERWRITE`: devolve o mesmo caminho (confirmação explícita é responsabilidade da UI).
    - `ASK`: lança `ArquivoJaExisteError` para a interface perguntar ao usuário.
    """
    if not path.exists():
        return path
    if policy is CollisionPolicy.OVERWRITE:
        return path
    if policy is CollisionPolicy.ASK:
        raise ArquivoJaExisteError(path)
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def validate_output_path(output: Path, source_pdf: Path | None = None) -> Path:
    """Valida e normaliza o caminho de saída (.mp3), sem criar arquivos."""
    try:
        resolved = output.expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise SaidaInvalidaError("Caminho de saída inválido.", detail=repr(exc)) from exc
    if resolved.suffix.lower() != ".mp3":
        raise SaidaInvalidaError("O arquivo de saída deve ter a extensão .mp3.")
    if resolved.is_dir():
        raise SaidaInvalidaError("O caminho de saída aponta para uma pasta, não para um arquivo.")
    parent = resolved.parent
    if not parent.is_dir():
        raise SaidaInvalidaError("A pasta de saída não existe.", detail=f"pasta={parent}")
    if not os.access(parent, os.W_OK):
        raise SaidaInvalidaError("Sem permissão de escrita na pasta de saída.")
    if source_pdf is not None and resolved == source_pdf.expanduser().resolve():
        raise SaidaInvalidaError("A saída não pode ser o próprio PDF de origem.")
    return resolved


@contextlib.contextmanager
def job_tempdir(prefix: str = "matraca-") -> Iterator[Path]:
    """Diretório temporário único por job, removido ao final (sucesso, erro ou cancelamento)."""
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if tmp.exists():
            # Não escondemos a falha: ela é registrada para diagnóstico.
            _log.warning("Falha ao remover temporário: %s", tmp)


def default_state_dir() -> Path:
    """Diretório padrão de estado/configurações do usuário; `MATRACA_STATE_DIR` o substitui."""
    override = os.environ.get("MATRACA_STATE_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return base / "matraca"
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state) if state else Path.home() / ".local" / "state"
    return base / "matraca"


def default_custom_strategies_path() -> Path:
    """Caminho do arquivo JSON de estratégias customizadas do usuário."""
    return default_state_dir() / "custom_strategies.json"


def default_log_dir() -> Path:
    """Diretório padrão de logs (documentado no README); `MATRACA_LOG_DIR` o substitui."""
    override = os.environ.get("MATRACA_LOG_DIR")
    if override:
        return Path(override)
    return default_state_dir() / "logs"
