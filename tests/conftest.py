"""Fixtures compartilhadas: PDFs sintéticos gerados por `scripts/make_fixtures.py`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_make_fixtures():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(
        "make_fixtures", ROOT / "scripts" / "make_fixtures.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["make_fixtures"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def make_fixtures():  # type: ignore[no-untyped-def]
    """Módulo `scripts/make_fixtures.py` carregado dinamicamente."""
    return _load_make_fixtures()


@pytest.fixture(scope="session")
def pdfs(tmp_path_factory: pytest.TempPathFactory, make_fixtures) -> dict[str, Path]:  # type: ignore[no-untyped-def]
    """Todas as fixtures rápidas, geradas uma vez por sessão."""
    out = tmp_path_factory.mktemp("sinteticos")
    return make_fixtures.build_all(out)  # type: ignore[no-any-return]
