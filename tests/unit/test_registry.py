"""Testes do registro de estratégias (RF-04), incluindo extensibilidade sem tocar UI/áudio."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from matraca.config import ExtractionConfig
from matraca.core.exceptions import MatracaError
from matraca.core.models import ExtractedBlock, ExtractedPage, ExtractionResult
from matraca.core.ports import PDFReader, PDFTextStrategy
from matraca.core.progress import CancellationToken, ProgressCallback
from matraca.extractors.registry import StrategyRegistry, default_registry

pytestmark = pytest.mark.unit


class FakeStrategy:
    """Estratégia falsa: prova que novas estratégias entram só pelo registro."""

    name = "fake"
    display_name = "Falsa"
    implemented = True

    def extract(
        self,
        reader: PDFReader,
        pages: Sequence[int],
        config: ExtractionConfig,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> ExtractionResult:
        bloco = ExtractedBlock("texto falso", pages[0], (0, 0, 1, 1))
        return ExtractionResult(pages=(ExtractedPage(pages[0], (bloco,)),), strategy_name=self.name)


def test_registro_padrao() -> None:
    reg = default_registry()
    assert [s.name for s in reg.selectable()] == ["concursos", "padrao"]
    assert [s.name for s in reg.all()] == ["concursos", "padrao", "lei_seca", "livro"]
    assert not reg.all()[2].implemented


def test_em_breve_nao_e_selecionavel() -> None:
    reg = default_registry()
    with pytest.raises(MatracaError):
        reg.get("lei_seca")
    with pytest.raises(MatracaError):
        reg.get("inexistente")


def test_estrategia_nova_so_precisa_ser_registrada() -> None:
    reg = default_registry()
    fake = FakeStrategy()
    assert isinstance(fake, PDFTextStrategy)
    reg.register(fake)
    assert reg.get("fake") is fake
    assert "fake" in [s.name for s in reg.selectable()]


def test_registro_duplicado_e_erro() -> None:
    reg = StrategyRegistry()
    reg.register(FakeStrategy())
    with pytest.raises(ValueError):
        reg.register(FakeStrategy())


def test_registros_sao_independentes() -> None:
    a, b = default_registry(), default_registry()
    a.register(FakeStrategy())
    assert "fake" not in [s.name for s in b.all()]
