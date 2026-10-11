"""Testes do serviço TextPipelineService (RF-09, RF-10)."""

from __future__ import annotations

import pytest

from matraca.core.models import BlockType, ExtractedBlock, ExtractedPage, ExtractionResult
from matraca.core.text_pipeline import TextPipelineService

pytestmark = pytest.mark.unit


def test_text_pipeline_service_alinhamento_e_estatisticas() -> None:
    service = TextPipelineService()
    blocos = (
        ExtractedBlock(
            "Art. 5º da CF/88.", page=1, bbox=(0, 0, 10, 10), block_type=BlockType.PARAGRAPH
        ),
        ExtractedBlock(
            "R$ 1.250,00 de taxa.", page=1, bbox=(0, 0, 10, 10), block_type=BlockType.PARAGRAPH
        ),
    )
    pagina = ExtractedPage(number=1, blocks=blocos)
    extracao = ExtractionResult(pages=(pagina,), strategy_name="padrao")

    narracao = service.process(extracao)

    assert len(narracao.paragraphs) == 2
    assert len(narracao.original_paragraphs) == 2
    assert narracao.paragraphs[0] == "Artigo quinto da Constituição Federal de oitenta e oito."
    assert narracao.paragraphs[1] == "mil duzentos e cinquenta reais de taxa."
    assert narracao.original_paragraphs[0] == "Art. 5º da CF/88."
    assert narracao.stats["paragraphs"] == 2
    assert narracao.stats["words"] > 0
    assert narracao.text.startswith("Artigo quinto")
    assert narracao.original_text.startswith("Art. 5º")
