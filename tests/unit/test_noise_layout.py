"""Testes unitários de ruído, layout e tratamento de tabelas/figuras com páginas sintéticas."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest

from matraca.config import ExtractionConfig
from matraca.core.models import BBox, BlockType, RawBlock, RawLine, RawPage
from matraca.extractors.default import DefaultStrategy
from matraca.extractors.layout import order_blocks
from matraca.extractors.noise import NoiseDetector, NoisePattern, repeat_key
from matraca.pdf.pymupdf_reader import PyMuPDFReader

pytestmark = pytest.mark.unit

W, H = 595.0, 842.0


def tb(
    text: str,
    bbox: BBox,
    *,
    direction: tuple[float, float] = (1.0, 0.0),
    color: int = 0,
    alpha: int = 255,
    size: float = 11.0,
) -> RawBlock:
    line = RawLine(text, bbox, direction=direction, font_size=size, color=color, alpha=alpha)
    return RawBlock(kind="text", bbox=bbox, lines=(line,))


def page(number: int, blocks: Sequence[RawBlock], **kw: object) -> RawPage:
    return RawPage(number=number, width=W, height=H, blocks=tuple(blocks), **kw)  # type: ignore[arg-type]


class FakeReader:
    """PDFReader falso a partir de páginas prontas."""

    def __init__(self, pages: Sequence[RawPage]) -> None:
        self.path = Path("falso.pdf")
        self._pages = {p.number: p for p in pages}

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def is_encrypted(self) -> bool:
        return False

    def metadata(self) -> dict[str, str]:
        return {}

    def read_page(self, number: int, *, with_tables: bool = False) -> RawPage:
        return self._pages[number]

    def render_page_thumbnail(self, number: int, *, max_dimension: int = 300) -> bytes:
        return b"\x89PNG\r\n\x1a\nfake_thumb"


# --- Ruído: sinais isolados nunca removem ---------------------------------------------------


def _detector(pages: Sequence[RawPage], **cfg: object) -> NoiseDetector:
    det = NoiseDetector(ExtractionConfig(**cfg))  # type: ignore[arg-type]
    det.fit(pages)
    return det


def test_so_proximidade_da_margem_nao_remove() -> None:
    rodape = tb("Nota do autor sobre o tema.", (72, 790, 300, 800))
    pg = page(1, [rodape])
    assert _detector([pg, page(2, [])]).classify(pg, rodape) is None


def test_so_repeticao_no_corpo_nao_remove() -> None:
    def corpo(n: int) -> RawPage:
        return page(n, [tb("Gabarito", (72, 300, 140, 312))])

    paginas = [corpo(i) for i in range(1, 6)]
    det = _detector(paginas)
    assert det.classify(paginas[0], paginas[0].blocks[0]) is None


def test_numeracao_no_corpo_sem_margem_nao_remove() -> None:
    bloco = tb("3/4", (72, 300, 100, 312))
    pg = page(1, [bloco])
    assert _detector([pg]).classify(pg, bloco) is None


def test_numero_isolado_na_margem_e_removido() -> None:
    bloco = tb("12", (290, 810, 300, 820))
    pg = page(1, [bloco])
    decisao = _detector([pg]).classify(pg, bloco)
    assert decisao is not None
    assert decisao.reason == "numero_de_pagina"


def test_so_rotacao_ou_so_cor_clara_nao_remove() -> None:
    rotacionado = tb("Texto vertical", (20, 300, 30, 500), direction=(0.0, -1.0))
    claro = tb("Texto cinza claro", (72, 300, 300, 312), color=0xCCCCCC)
    pg = page(1, [rotacionado, claro])
    det = _detector([pg])
    assert det.classify(pg, rotacionado) is None
    assert det.classify(pg, claro) is None


def test_rotacionado_e_claro_juntos_sao_marca_dagua() -> None:
    marca = tb("RASCUNHO", (300, 200, 330, 600), direction=(0.0, -1.0), color=0xDDDDDD)
    pg = page(1, [marca])
    decisao = _detector([pg]).classify(pg, marca)
    assert decisao is not None
    assert decisao.reason == "marca_dagua"


def test_texto_branco_em_faixa_escura_nao_vira_marca_dagua() -> None:
    titulo = tb("TITULO EM FAIXA", (72, 20, 300, 40), color=0xFFFFFF)
    pg = page(1, [titulo])
    assert _detector([pg]).classify(pg, titulo) is None


def test_padrao_configurado_exige_segundo_sinal() -> None:
    padrao = NoisePattern.compile("marca_licenca", r"CPF\s*\d{3}")
    det = NoiseDetector(ExtractionConfig(), [padrao])
    corpo = tb("Questão sobre CPF 123 citado no enunciado.", (72, 300, 400, 312))
    margem = tb("Licença CPF 123", (72, 810, 200, 820))
    pg = page(1, [corpo, margem])
    det.fit([pg])
    assert det.classify(pg, corpo) is None
    decisao = det.classify(pg, margem)
    assert decisao is not None
    assert decisao.reason == "marca_licenca"


def test_padrao_invalido_gera_erro_claro() -> None:
    with pytest.raises(ValueError, match="inválida"):
        NoisePattern.compile("x", "(")


def test_repeat_key_troca_digitos() -> None:
    assert repeat_key("Página 12  de 300") == "página # de #"


# --- Layout --------------------------------------------------------------------------------


def test_layout_muitas_colunas_volta_a_ordem_nativa_com_aviso() -> None:
    blocos = [tb(f"c{i}", (50 + i * 100, 100, 90 + i * 100, 200)) for i in (4, 3, 2, 1, 0)]
    resultado = order_blocks(blocos, W)
    assert [b.text for b in resultado.blocks] == ["c4", "c3", "c2", "c1", "c0"]
    assert resultado.warnings


def test_layout_grupos_empilhados_nao_sao_colunas() -> None:
    topo_esq = tb("TOPO", (72, 100, 250, 120))
    baixo_dir = tb("BAIXO", (320, 500, 500, 520))
    resultado = order_blocks([baixo_dir, topo_esq], W)
    assert [b.text for b in resultado.blocks] == ["TOPO", "BAIXO"]
    assert resultado.columns == 1


def test_layout_duas_colunas() -> None:
    blocos = [
        tb("D1", (320, 100, 500, 140)),
        tb("E1", (72, 100, 250, 140)),
        tb("D2", (320, 160, 500, 200)),
        tb("E2", (72, 160, 250, 200)),
    ]
    resultado = order_blocks(blocos, W)
    assert [b.text for b in resultado.blocks] == ["E1", "E2", "D1", "D2"]
    assert resultado.columns == 2


def test_layout_desligado_mantem_ordem_nativa() -> None:
    blocos = [tb("B", (72, 300, 250, 320)), tb("A", (72, 100, 250, 120))]
    assert [b.text for b in order_blocks(blocos, W, detect_columns=False).blocks] == ["B", "A"]


# --- Tabelas e figuras (RF-07) ---------------------------------------------------------------


def _pagina_com_tabela_e_figura() -> RawPage:
    return page(
        1,
        [
            tb("Texto antes da tabela, em parágrafo normal.", (72, 100, 400, 120)),
            tb("Célula A1", (80, 200, 150, 215)),
            tb("Célula B1", (160, 200, 230, 215)),
            tb("Texto depois da tabela, em parágrafo normal.", (72, 400, 400, 420)),
            RawBlock(kind="image", bbox=(72, 500, 300, 700)),
        ],
        table_bboxes=((72.0, 190.0, 300.0, 230.0),),
    )


def _extrair(config: ExtractionConfig):  # type: ignore[no-untyped-def]
    reader = FakeReader([_pagina_com_tabela_e_figura()])
    return DefaultStrategy().extract(reader, [1], config)


def test_tabela_marker_e_figura_ignorada() -> None:
    res = _extrair(ExtractionConfig(tables="marker", figures="ignore"))
    textos = [b.text for b in res.pages[0].blocks]
    assert "[Tabela nesta página]" in textos
    assert not any("Célula" in t for t in textos)
    assert any("1 figura" in w and "não foi" in w for w in res.warnings)
    assert res.pages[0].blocks[1].block_type is BlockType.TABLE
    assert textos.index("[Tabela nesta página]") == 1  # na posição do fluxo


def test_tabela_ignore_descarta_sem_marcador() -> None:
    res = _extrair(ExtractionConfig(tables="ignore"))
    textos = [b.text for b in res.pages[0].blocks]
    assert len(textos) == 2
    assert any("tabela" in w and "não foi" in w for w in res.warnings)


def test_tabela_linear_mantem_texto() -> None:
    res = _extrair(ExtractionConfig(tables="linear"))
    assert any("Célula A1" in b.text for b in res.pages[0].blocks)


def test_figura_marker() -> None:
    res = _extrair(ExtractionConfig(figures="marker"))
    tipos = [b.block_type for b in res.pages[0].blocks]
    assert BlockType.FIGURE_MARKER in tipos


def test_find_tables_real_nao_quebra(pdfs: dict[str, Path]) -> None:
    with PyMuPDFReader(pdfs["uma_coluna"]) as reader:
        assert isinstance(reader.read_page(1, with_tables=True).table_bboxes, tuple)
