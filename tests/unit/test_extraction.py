"""Testes do leitor PyMuPDF, do serviço de PDF e da extração (RF-01/02/05-08)."""

from __future__ import annotations

from pathlib import Path

import pytest

from matraca.config import ExtractionConfig
from matraca.core.exceptions import PDFInvalidoError, PDFProtegidoError, PDFSemTextoError
from matraca.core.models import BlockType, ExtractionResult
from matraca.core.pdf_service import PDFService, sample_indices
from matraca.core.progress import CancellationToken, ProgressEvent
from matraca.extractors.default import DefaultStrategy
from matraca.extractors.estrategia_concursos import ConcursosStrategy
from matraca.pdf.pymupdf_reader import PyMuPDFReader

pytestmark = pytest.mark.unit


def _extract(
    path: Path,
    pages: list[int] | None = None,
    strategy: DefaultStrategy | None = None,
    config: ExtractionConfig | None = None,
) -> ExtractionResult:
    strategy = strategy or DefaultStrategy()
    with PyMuPDFReader(path) as reader:
        selected = pages or list(range(1, reader.page_count + 1))
        return strategy.extract(reader, selected, config or ExtractionConfig())


def _text(result: ExtractionResult) -> str:
    return "\n".join(b.text for p in result.pages for b in p.blocks)


# --- Validação (RF-01) -------------------------------------------------------------------


def test_pdf_valido_inspeciona(pdfs: dict[str, Path]) -> None:
    info = PDFService(PyMuPDFReader).inspect(pdfs["uma_coluna"])
    assert info.page_count == 3
    assert info.has_text_layer
    assert not info.is_encrypted


def test_pdf_protegido(pdfs: dict[str, Path]) -> None:
    with pytest.raises(PDFProtegidoError):
        PyMuPDFReader(pdfs["protegido"])


def test_pdf_corrompido(pdfs: dict[str, Path]) -> None:
    with pytest.raises(PDFInvalidoError):
        PyMuPDFReader(pdfs["corrompido"])


def test_pdf_vazio_zero_bytes(pdfs: dict[str, Path]) -> None:
    with pytest.raises(PDFInvalidoError):
        PDFService(PyMuPDFReader).open(pdfs["vazio"])


def test_pdf_inexistente(tmp_path: Path) -> None:
    with pytest.raises(PDFInvalidoError):
        PyMuPDFReader(tmp_path / "nao_existe.pdf")


def test_pasta_nao_e_pdf(tmp_path: Path) -> None:
    with pytest.raises(PDFInvalidoError):
        PyMuPDFReader(tmp_path)


def test_sem_camada_de_texto_detectado_na_inspecao(pdfs: dict[str, Path]) -> None:
    assert not PDFService(PyMuPDFReader).inspect(pdfs["somente_imagem"]).has_text_layer


def test_leitor_fecha_o_arquivo(pdfs: dict[str, Path]) -> None:
    with PyMuPDFReader(pdfs["uma_coluna"]) as reader:
        assert reader.page_count == 3
    assert reader._doc.is_closed


def test_sample_indices() -> None:
    assert sample_indices(3, 8) == [1, 2, 3]
    amostra = sample_indices(500, 40)
    assert amostra[0] == 1
    assert amostra[-1] == 500
    assert len(amostra) <= 40
    assert amostra == sorted(set(amostra))


# --- Digitalizados e sem texto (RF-08) -------------------------------------------------------


def test_somente_imagem_levanta_sem_texto(pdfs: dict[str, Path]) -> None:
    with pytest.raises(PDFSemTextoError):
        _extract(pdfs["somente_imagem"])


def test_pagina_em_branco_levanta_sem_texto(pdfs: dict[str, Path]) -> None:
    with pytest.raises(PDFSemTextoError):
        _extract(pdfs["pagina_em_branco"])


def test_pagina_isolada_sem_texto_e_apenas_aviso(tmp_path: Path, make_fixtures) -> None:  # type: ignore[no-untyped-def]
    import pymupdf

    doc = pymupdf.open()
    doc.new_page().insert_text((72, 100), "Primeira página com texto suficiente")
    doc.new_page()  # em branco
    caminho = tmp_path / "misto.pdf"
    doc.save(caminho)
    doc.close()
    result = _extract(caminho)
    assert result.pages[1].empty
    assert any("Página 2" in w for w in result.warnings)


# --- Seleção e ordem (RF-02) -----------------------------------------------------------------


def test_processa_apenas_paginas_selecionadas_na_ordem(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["uma_coluna"], pages=[3, 1])
    assert [p.number for p in result.pages] == [3, 1]
    assert "página 3" in result.pages[0].blocks[0].text
    assert result.stats["pages"] == 2


def test_progresso_e_cancelamento(pdfs: dict[str, Path]) -> None:
    eventos: list[ProgressEvent] = []
    with PyMuPDFReader(pdfs["uma_coluna"]) as reader:
        DefaultStrategy().extract(reader, [1, 2, 3], ExtractionConfig(), progress=eventos.append)
    assert [e.current for e in eventos] == [1, 2, 3]

    token = CancellationToken()
    token.cancel()
    from matraca.core.exceptions import CancelamentoError

    with PyMuPDFReader(pdfs["uma_coluna"]) as reader, pytest.raises(CancelamentoError):
        DefaultStrategy().extract(reader, [1, 2, 3], ExtractionConfig(), cancel=token)


# --- Ordem de leitura (RF-06) ---------------------------------------------------------------


def test_uma_coluna_preserva_quebras_de_linha(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["uma_coluna"], pages=[1])
    texto = _text(result)
    assert "Parágrafo um" in texto
    assert texto.index("Parágrafo um") < texto.index("Parágrafo dois")
    assert "\n" in result.pages[0].blocks[0].text


def test_duas_colunas_ordem_coluna_a_coluna(pdfs: dict[str, Path]) -> None:
    texto = _text(_extract(pdfs["duas_colunas"], pages=[1]))
    ordem = [texto.index(m) for m in ("ESQUERDA-1", "ESQUERDA-2", "DIREITA-1", "DIREITA-2")]
    assert ordem == sorted(ordem)


def test_titulo_largura_total_antes_das_colunas(pdfs: dict[str, Path]) -> None:
    texto = _text(_extract(pdfs["duas_colunas"], pages=[2]))
    ordem = [
        texto.index(m)
        for m in ("TITULO-LARGURA-TOTAL", "ESQUERDA-1", "ESQUERDA-2", "DIREITA-1", "DIREITA-2")
    ]
    assert ordem == sorted(ordem)


def test_caixa_lateral_nao_quebra_paragrafos(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["duas_colunas"], pages=[3])
    textos = [b.text for b in result.pages[0].blocks]
    assert any("PRINCIPAL-1" in t and "PRINCIPAL-2" not in t for t in textos)
    assert any(t.startswith("CAIXA-LATERAL") for t in textos)
    # nenhum bloco mistura a caixa com o texto principal
    assert not any("CAIXA-LATERAL" in t and "PRINCIPAL" in t for t in textos)


def test_sem_deteccao_de_colunas_mantem_ordem_nativa(pdfs: dict[str, Path]) -> None:
    config = ExtractionConfig(detect_columns=False)
    texto = _text(_extract(pdfs["duas_colunas"], pages=[1], config=config))
    assert "ESQUERDA-1" in texto  # funciona; a ordem é a nativa do PDF


# --- Ruído (RF-05) ----------------------------------------------------------------------------


def test_remove_cabecalho_rodape_e_numeracao(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["cabecalho_rodape"])
    texto = _text(result)
    assert "Prof. Fulano" not in texto
    assert "Página 3 de 6" not in texto
    assert "CORPO-3" in texto
    assert result.stats["ruido_numero_de_pagina"] == 6
    assert result.noise_records
    assert all(r.snippet for r in result.noise_records)


def test_marca_de_licenca_removida_sem_ler_dados_pessoais(pdfs: dict[str, Path]) -> None:
    for estrategia in (DefaultStrategy(), ConcursosStrategy()):
        texto = _text(_extract(pdfs["cabecalho_rodape"], strategy=estrategia))
        assert "MARIA SOUZA" not in texto
        assert "111.222.333" not in texto


def test_remocao_desativada_preserva_tudo(pdfs: dict[str, Path]) -> None:
    config = ExtractionConfig(remove_headers_footers=False)
    result = _extract(pdfs["cabecalho_rodape"], config=config)
    texto = _text(result)
    assert "Prof. Fulano" in texto
    assert "Página 3 de 6" in texto
    assert not result.noise_records


def test_nota_de_rodape_juridica_nao_e_removida(pdfs: dict[str, Path]) -> None:
    """Teste negativo obrigatório: conteúdo legítimo na margem inferior permanece."""
    for estrategia in (DefaultStrategy(), ConcursosStrategy()):
        result = _extract(pdfs["nota_rodape_juridica"], strategy=estrategia)
        texto = _text(result)
        assert "art. 5º, inciso II" in texto
        assert "Lei 8.112/90, art. 41" in texto
        assert "Súmula Vinculante 13" in texto
        assert "Lei 14.133/21, art. 5º" in texto
        # só os números de página (isolados na margem) foram removidos
        assert result.stats["ruido_numero_de_pagina"] == 4
        assert result.stats.get("ruido_cabecalho_rodape", 0) == 0


def test_registros_de_ruido_nao_guardam_texto_integral(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["cabecalho_rodape"])
    longo = "Direito Constitucional - Prof. Fulano de Tal"
    assert all(longo not in r.snippet for r in result.noise_records)


# --- Texto jurídico e estratégia Concursos -------------------------------------------------------


def test_texto_juridico_preservado(pdfs: dict[str, Path]) -> None:
    texto = _text(_extract(pdfs["texto_juridico"]))
    for trecho in ("Art. 5º", "§ 1º", "Lei 8.666/93", "I - homens"):
        assert trecho in texto


def test_concursos_formata_banca_ano_inequivoco(pdfs: dict[str, Path]) -> None:
    texto = _text(_extract(pdfs["texto_juridico"], strategy=ConcursosStrategy()))
    assert "Questão da banca CESPE, de 2019." in texto
    assert "(CESPE/2019)" not in texto
    padrao = _text(_extract(pdfs["texto_juridico"]))
    assert "(CESPE/2019)" in padrao  # estratégia Padrão não altera


def test_classificacao_de_blocos(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["texto_juridico"])
    tipos = {b.block_type for b in result.pages[0].blocks}
    assert tipos <= set(BlockType)


def test_estatisticas_e_nome_da_estrategia(pdfs: dict[str, Path]) -> None:
    result = _extract(pdfs["uma_coluna"], strategy=ConcursosStrategy())
    assert result.strategy_name == "concursos"
    assert result.stats["pages"] == 3
    assert result.stats["chars"] == result.total_chars


def test_render_page_thumbnail_retorna_png_valido(pdfs: dict[str, Path]) -> None:
    with PyMuPDFReader(pdfs["uma_coluna"]) as reader:
        thumb = reader.render_page_thumbnail(1, max_dimension=200)
        assert isinstance(thumb, bytes)
        assert thumb.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(thumb) > 100

        with pytest.raises(PDFInvalidoError, match="fora do documento"):
            reader.render_page_thumbnail(999)


def test_pdf_service_render_thumbnails_lote(pdfs: dict[str, Path]) -> None:
    service = PDFService(PyMuPDFReader)
    thumbs = service.render_thumbnails(pdfs["uma_coluna"], [1, 2], max_dimension=150)
    assert set(thumbs.keys()) == {1, 2}
    for data in thumbs.values():
        assert isinstance(data, bytes)
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
