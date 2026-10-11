"""Testes de invariantes do pipeline de normalização (A.13.3)."""

from __future__ import annotations

import pytest

from matraca.text.normalization import PIPELINE_STEPS, normalize_text

pytestmark = pytest.mark.unit


def test_ordem_estrita_do_pipeline_fixada() -> None:
    """Verifica que a ordem das etapas puras é exatamente a documentada na arquitetura."""
    etapas = [s.name for s in PIPELINE_STEPS]
    esperado = [
        "cleanup_unicode",
        "reconstruct_lines",
        "legal_abbreviations",
        "laws_and_dates",
        "currency_and_percents",
        "articles_and_incisos",
        "numbers",
        "acronyms",
        "adjust_prosody",
    ]
    assert etapas == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Texto simples",
        "Art. 5º da CF/88",
        "12345",
        "   ",
        "\n\n\n",
        "§ 1º e inc. II",
        "R$ 50,00 e 10%",
    ],
)
def test_invariante_determinismo(texto: str) -> None:
    """A normalização é estritamente determinística (mesma entrada -> mesma saída)."""
    res1, stats1, _ = normalize_text(texto)
    res2, stats2, _ = normalize_text(texto)
    assert res1 == res2
    assert stats1 == stats2


@pytest.mark.parametrize(
    "texto",
    [
        "a",
        "Martin e Particular",
        "Artigo quinto",
        "Lei 8.666/93",
        "Qualquer texto que contenha caracteres não brancos",
    ],
)
def test_invariante_nunca_retorna_vazio_para_entrada_nao_vazia(texto: str) -> None:
    """A normalização nunca devolve texto vazio para entrada com conteúdo."""
    res, _, _ = normalize_text(texto)
    assert len(res.strip()) > 0


@pytest.mark.parametrize(
    ("palavra", "contexto"),
    [
        ("Martin", "O professor Martin comentou o julgado."),
        ("Particular", "Um interesse particular foi atendido."),
        ("Cart.", "Cart. de Notas e Protestos."),
        ("Artigo", "O Artigo já estava por extenso."),
        ("Parágrafo", "O Parágrafo também estava por extenso."),
        ("Participante", "O participante foi aprovado."),
        ("Apartamento", "Alugou um apartamento."),
    ],
)
def test_invariante_sem_substituicao_parcial_em_palavras_maiores(
    palavra: str, contexto: str
) -> None:
    """Palavras que contêm substrings de abreviações não sofrem substituição corrompida."""
    res, _, _ = normalize_text(contexto)
    assert palavra in res or palavra.lower() in res.lower()


@pytest.mark.parametrize(
    "texto",
    [
        "Artigo quinto, inciso dois",
        "Lei oito mil seiscentos e sessenta e seis, de noventa e três",
        "dez por cento",
        "mil duzentos e cinquenta reais",
        "primeiro de fevereiro de dois mil e vinte",
        "Texto comum sem regras numéricas.",
    ],
)
def test_invariante_idempotencia_em_textos_ja_normalizados(texto: str) -> None:
    """Após uma passagem completa, passar novamente um texto já normalizado é idempotente."""
    uma_vez, _, _ = normalize_text(texto)
    duas_vezes, _, _ = normalize_text(uma_vez)
    assert uma_vez == duas_vezes
