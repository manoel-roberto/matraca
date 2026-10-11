"""Testes Golden de normalização (RF-09, A.13.3).

Lê os casos de teste a partir de `tests/golden/casos_normalizacao.tsv`.
Mínimo exigido pelo prompt mestre: 80 casos.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from matraca.text.normalization import normalize_text

pytestmark = pytest.mark.unit

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "golden" / "casos_normalizacao.tsv"


def load_golden_cases() -> list[tuple[str, str, str]]:
    cases: list[tuple[str, str, str]] = []
    lines = GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    assert header[0] == "entrada" and header[1] == "saida_esperada"

    for row in lines[1:]:
        if not row.strip():
            continue
        parts = row.split("\t")
        if len(parts) >= 2:
            entrada = parts[0].replace("\\n", "\n")
            saida = parts[1].replace("\\n", "\n")
            obs = parts[2] if len(parts) > 2 else ""
            cases.append((entrada, saida, obs))
    return cases


ALL_CASES = load_golden_cases()


def test_minimo_oitenta_casos_golden() -> None:
    assert len(ALL_CASES) >= 80, (
        f"Exigem-se pelo menos 80 casos golden, encontrados: {len(ALL_CASES)}"
    )


@pytest.mark.parametrize(
    ("entrada", "esperado", "obs"),
    ALL_CASES,
    ids=[f"caso_{i:02d}_{c[2][:30]}" for i, c in enumerate(ALL_CASES, 1)],
)
def test_golden_cases(entrada: str, esperado: str, obs: str) -> None:
    norm, _stats, _warns = normalize_text(entrada)
    assert norm == esperado, f"Falha no caso '{obs}'. Entrada: {entrada!r}"
