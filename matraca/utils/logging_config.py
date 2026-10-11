"""Configuração de logging sem conteúdo de PDF (A.13.8).

Nada é configurado na importação; chame `setup_logging` explicitamente a partir das entradas.
"""

from __future__ import annotations

import hashlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from matraca.utils.paths import default_log_dir

_HANDLER_MARK = "_matraca_handler"
LOG_FILENAME = "matraca.log"


def describe_text(text: str) -> str:
    """Descreve um texto por contagem e hash curto, para logar sem expor o conteúdo."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"texto(len={len(text)}, sha256={digest})"


def setup_logging(
    log_dir: Path | None = None, *, debug: bool = False, console: bool = False
) -> Path:
    """Configura o logger raiz `matraca` com rotação de arquivo; idempotente.

    Devolve o caminho do arquivo de log. INFO por padrão; DEBUG só com `debug=True`
    (mesmo em DEBUG, o código deve logar contagens/hashes, nunca texto integral).
    """
    directory = log_dir or default_log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    log_file = directory / LOG_FILENAME

    logger = logging.getLogger("matraca")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            logger.removeHandler(handler)
            handler.close()

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    setattr(file_handler, _HANDLER_MARK, True)
    logger.addHandler(file_handler)

    if console:
        stream = logging.StreamHandler()
        stream.setFormatter(fmt)
        setattr(stream, _HANDLER_MARK, True)
        logger.addHandler(stream)
    return log_file
