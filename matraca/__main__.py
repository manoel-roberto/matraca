"""Ponto de entrada quando invocado como módulo (python -m matraca)."""

from __future__ import annotations

import sys

from matraca.cli import main

if __name__ == "__main__":
    sys.exit(main())
