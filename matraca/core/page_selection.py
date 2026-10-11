"""Seleção de páginas por expressão (RF-03, A.13.1).

Gramática aceita: lista de itens separados por vírgula (`,`) ou ponto e vírgula (`;`);
cada item é um número (`7`) ou um intervalo fechado (`5-10`). Espaços extras são ignorados.
Traços Unicode (– — ‑ ‐ −) são aceitos como hífen e normalizados (decisão documentada no ADR-008).
Páginas começam em 1. O resultado é deduplicado e ordenado de forma crescente.
Entrada vazia ou inválida é sempre erro: nunca vira "todas as páginas".
"""

from __future__ import annotations

import re

from matraca.core.exceptions import SelecaoPaginasError
from matraca.core.models import PageSelection

_DASHES = str.maketrans(dict.fromkeys("\u2010\u2011\u2012\u2013\u2014\u2212", "-"))
_NUMBER = re.compile(r"[0-9]+")
_RANGE = re.compile(r"([0-9]+)\s*-\s*([0-9]+)")
_MAX_DIGITS = 9  # evita conversões de inteiros gigantes antes de comparar com o total


def _to_int(digits: str, token: str) -> int:
    if len(digits) > _MAX_DIGITS:
        raise SelecaoPaginasError(f"O número em “{token}” é grande demais.")
    return int(digits)


def parse_page_selection(expr: str, total_pages: int) -> PageSelection:
    """Interpreta `expr` e devolve a seleção validada contra `total_pages`.

    Lança `SelecaoPaginasError` (mensagem em pt-BR apontando o item problemático).
    """
    if total_pages < 1:
        raise SelecaoPaginasError("O documento não tem páginas.")
    normalized = expr.translate(_DASHES).replace(";", ",")
    if not normalized.strip():
        raise SelecaoPaginasError("Informe as páginas (ex.: 1, 3, 5-10) ou escolha “todas”.")

    pages: set[int] = set()
    for raw in normalized.split(","):
        token = raw.strip()
        if not token:
            raise SelecaoPaginasError("Há um item vazio na lista de páginas (vírgulas repetidas?).")
        if _NUMBER.fullmatch(token):
            page = _to_int(token, token)
            _check_bounds(page, total_pages, token)
            pages.add(page)
            continue
        match = _RANGE.fullmatch(token)
        if not match:
            raise SelecaoPaginasError(f"Item inválido na seleção de páginas: “{token}”.")
        start = _to_int(match.group(1), token)
        end = _to_int(match.group(2), token)
        _check_bounds(start, total_pages, token)
        _check_bounds(end, total_pages, token)
        if start > end:
            raise SelecaoPaginasError(f"Intervalo invertido: “{token}” (início maior que o fim).")
        # Limites validados por aritmética acima: o intervalo tem no máximo `total_pages` itens.
        pages.update(range(start, end + 1))

    return PageSelection(
        expression=expr.strip(), pages=tuple(sorted(pages)), total_pages=total_pages
    )


def _check_bounds(page: int, total_pages: int, token: str) -> None:
    if page < 1:
        raise SelecaoPaginasError(f"As páginas começam em 1: “{token}”.")
    if page > total_pages:
        raise SelecaoPaginasError(
            f"A página {page} (em “{token}”) não existe: o documento tem {total_pages} página(s)."
        )


def describe_selection(selection: PageSelection) -> str:
    """Texto para a UI: quantas páginas serão processadas."""
    n = selection.count
    if n == 1:
        return "1 página será processada"
    return f"{n} páginas serão processadas"
