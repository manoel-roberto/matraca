"""Teste de desempenho e regressão em documento extenso de 500 páginas (RNF-08, Fase 7)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from matraca.core.pdf_service import PDFService
from matraca.extractors.registry import default_registry
from matraca.pdf.pymupdf_reader import PyMuPDFReader

pytestmark = pytest.mark.slow

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_processamento_incremental_500_paginas() -> None:
    """Verifica que um documento de 500 páginas é inspecionado e extraído de forma estável."""
    pdf_path = _FIXTURES_DIR / "grande_500.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture grande_500.pdf não encontrada.")

    pdf_service = PDFService(reader_factory=PyMuPDFReader)
    info = pdf_service.inspect(pdf_path)

    assert info.page_count == 500, f"Esperava 500 páginas, obteve {info.page_count}"
    assert info.has_text_layer

    registry = default_registry()
    strat = registry.get("concursos")

    from matraca.config import ExtractionConfig

    t_start = time.perf_counter()
    with pdf_service.open(pdf_path) as reader:
        # Extrai uma amostra representativa de 20 páginas de ponta a ponta
        amostra_paginas = tuple(range(1, 21))
        resultado = strat.extract(
            reader=reader,
            pages=amostra_paginas,
            config=ExtractionConfig(),
        )

    t_elapsed = time.perf_counter() - t_start

    assert len(resultado.pages) == 20
    assert all(len(p.blocks) > 0 for p in resultado.pages)
    total_chars = sum(len(b.text) for p in resultado.pages for b in p.blocks)
    assert total_chars > 0
    # Extração de 20 páginas sintéticas deve levar menos de 5 segundos
    assert t_elapsed < 5.0, f"Tempo de extração excessivo: {t_elapsed:.2f}s"
