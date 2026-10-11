"""Testes da seleção de páginas (RF-03)."""

from __future__ import annotations

import pytest

from matraca.core.exceptions import SelecaoPaginasError
from matraca.core.models import PageSelection
from matraca.core.page_selection import describe_selection, parse_page_selection

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("expr", "total", "esperado"),
    [
        ("1", 10, (1,)),
        ("10", 10, (10,)),  # última página
        ("1", 1, (1,)),  # total = 1
        ("1-1", 1, (1,)),
        ("1, 3, 5-10", 20, (1, 3, 5, 6, 7, 8, 9, 10)),
        ("1,3,5-7", 20, (1, 3, 5, 6, 7)),
        ("  2 ,  4 - 6  ", 10, (2, 4, 5, 6)),
        ("1-5, 3-7", 10, (1, 2, 3, 4, 5, 6, 7)),  # sobreposição
        ("5, 5, 5", 10, (5,)),  # duplicatas
        ("9, 2, 5", 10, (2, 5, 9)),  # ordena crescente
        ("8-10, 1-2", 10, (1, 2, 8, 9, 10)),
        ("1;3;5-6", 10, (1, 3, 5, 6)),  # ponto e vírgula
        ("1, 3; 5", 10, (1, 3, 5)),
        ("2–4", 10, (2, 3, 4)),  # en dash
        ("2—4", 10, (2, 3, 4)),  # em dash
        ("2‑4", 10, (2, 3, 4)),  # hífen não separável
        ("2−4", 10, (2, 3, 4)),  # sinal de menos
        ("1-10", 10, tuple(range(1, 11))),
        ("007", 10, (7,)),  # zeros à esquerda
    ],
)
def test_expressoes_validas(expr: str, total: int, esperado: tuple[int, ...]) -> None:
    selecao = parse_page_selection(expr, total)
    assert selecao.pages == esperado
    assert selecao.total_pages == total
    assert selecao.count == len(esperado)


@pytest.mark.parametrize(
    ("expr", "total"),
    [
        ("", 10),
        ("   ", 10),
        ("0", 10),
        ("-1", 10),
        ("-5", 10),
        ("5-", 10),
        ("10-5", 10),
        ("1,,2", 10),
        (",1", 10),
        ("1,", 10),
        ("a-b", 10),
        ("abc", 10),
        ("1.5", 10),
        ("1 2", 10),
        ("11", 10),
        ("1-11", 10),
        ("0-3", 10),
        ("1--3", 10),
        ("1-2-3", 10),
        ("9" * 50, 10),  # número absurdamente grande
        ("1-" + "9" * 400, 10),
        ("²", 10),  # dígito Unicode não ASCII
        ("1/3", 10),
        ("todas", 10),
        ("1", 0),  # documento sem páginas
    ],
)
def test_expressoes_invalidas_nunca_viram_todas(expr: str, total: int) -> None:
    with pytest.raises(SelecaoPaginasError):
        parse_page_selection(expr, total)


def test_mensagem_aponta_o_token_problematico() -> None:
    with pytest.raises(SelecaoPaginasError) as exc:
        parse_page_selection("1, 3, x7, 9", 10)
    assert "x7" in exc.value.user_message


def test_mensagem_de_pagina_inexistente_informa_total() -> None:
    with pytest.raises(SelecaoPaginasError) as exc:
        parse_page_selection("1-50", 10)
    assert "10" in exc.value.user_message


def test_intervalo_enorme_nao_materializa_antes_de_validar() -> None:
    # 999999999 > total: rejeitado por aritmética, sem criar range gigante
    with pytest.raises(SelecaoPaginasError):
        parse_page_selection("1-999999999", 10)


def test_todas_e_acao_explicita_separada() -> None:
    selecao = PageSelection.all(4)
    assert selecao.pages == (1, 2, 3, 4)


def test_descricao_para_ui() -> None:
    assert describe_selection(parse_page_selection("3", 5)) == "1 página será processada"
    assert describe_selection(parse_page_selection("1-3", 5)) == "3 páginas serão processadas"
