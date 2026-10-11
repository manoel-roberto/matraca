"""Gera PDFs sintéticos de teste com PyMuPDF (sem binários versionados).

Uso: python scripts/make_fixtures.py [diretório_de_saída]

Os construtores são registrados em `BUILDERS` (nome -> função que recebe o diretório e
devolve o caminho do PDF criado). Os construtores das fixtures 1-10 do prompt mestre
(A.13.9) são adicionados na Fase 2.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

BUILDERS: dict[str, Callable[[Path], Path]] = {}

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "sinteticos"


def build_all(out_dir: Path) -> dict[str, Path]:
    """Gera todas as fixtures registradas e devolve nome -> caminho."""
    out_dir.mkdir(parents=True, exist_ok=True)
    return {name: builder(out_dir) for name, builder in BUILDERS.items()}


def main(argv: list[str]) -> int:
    """Ponto de entrada de linha de comando."""
    out_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUT
    built = build_all(out_dir)
    for name, path in built.items():
        print(f"{name}: {path}")
    print(f"{len(built)} fixture(s) em {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
