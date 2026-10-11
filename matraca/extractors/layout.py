"""Ordem de leitura por colunas (RF-06).

Algoritmo, por página:
1. Blocos de largura quase total (títulos) separam "faixas" verticais.
2. Dentro de cada faixa, agrupam-se os blocos por sobreposição horizontal; se houver 2+
   grupos separados por um vão vertical contínuo e que se sobrepõem em altura, lê-se coluna a
   coluna (e, dentro da coluna, de cima para baixo).
3. Se a confiança for baixa (muitas colunas), volta-se à ordem nativa do PDF e emite-se aviso.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from matraca.core.models import RawBlock

FULL_WIDTH_RATIO = 0.55  # fração da largura da página a partir da qual o bloco é "de largura total"
MIN_COLUMN_GAP = 10.0  # pontos
MAX_COLUMNS = 3
MIN_VERTICAL_OVERLAP = 0.3


@dataclass(frozen=True)
class LayoutResult:
    """Blocos em ordem de leitura, número de colunas detectado e avisos."""

    blocks: tuple[RawBlock, ...]
    columns: int
    warnings: tuple[str, ...] = ()


def _y_order(blocks: Sequence[RawBlock]) -> list[RawBlock]:
    return sorted(blocks, key=lambda b: (b.bbox[1], b.bbox[0]))


def _clusters(blocks: Sequence[RawBlock]) -> list[list[RawBlock]]:
    """Agrupa blocos cujos intervalos horizontais se sobrepõem (ou distam < MIN_COLUMN_GAP)."""
    clusters: list[list[RawBlock]] = []
    right_edges: list[float] = []
    for block in sorted(blocks, key=lambda b: b.bbox[0]):
        x0, _, x1, _ = block.bbox
        if clusters and x0 < right_edges[-1] + MIN_COLUMN_GAP:
            clusters[-1].append(block)
            right_edges[-1] = max(right_edges[-1], x1)
        else:
            clusters.append([block])
            right_edges.append(x1)
    return clusters


def _span(blocks: Sequence[RawBlock]) -> tuple[float, float]:
    return min(b.bbox[1] for b in blocks), max(b.bbox[3] for b in blocks)


def _overlap_ratio(a: tuple[float, float], b: tuple[float, float]) -> float:
    inter = min(a[1], b[1]) - max(a[0], b[0])
    smaller = min(a[1] - a[0], b[1] - b[0])
    return inter / smaller if smaller > 0 and inter > 0 else 0.0


def _order_band(
    band: Sequence[RawBlock], native: dict[int, int]
) -> tuple[list[RawBlock], int, str]:
    """Ordena uma faixa; devolve (blocos, nº de colunas, aviso opcional)."""
    clusters = _clusters(band)
    if len(clusters) == 1:
        return _y_order(band), 1, ""
    if len(clusters) > MAX_COLUMNS:
        ordered = sorted(band, key=lambda b: native[id(b)])
        return ordered, 1, "Layout complexo: ordem de leitura nativa do PDF mantida."
    spans = [_span(c) for c in clusters]
    if any(
        _overlap_ratio(spans[i], spans[i + 1]) < MIN_VERTICAL_OVERLAP for i in range(len(spans) - 1)
    ):
        return _y_order(band), 1, ""  # grupos empilhados, não colunas lado a lado
    ordered_cols: list[RawBlock] = []
    for cluster in clusters:
        ordered_cols.extend(_y_order(cluster))
    return ordered_cols, len(clusters), ""


def order_blocks(
    blocks: Sequence[RawBlock], page_width: float, *, detect_columns: bool = True
) -> LayoutResult:
    """Ordena `blocks` (de texto) na ordem de leitura provável."""
    items = list(blocks)
    if len(items) < 2 or not detect_columns or page_width <= 0:
        return LayoutResult(tuple(items), 1)  # ordem nativa do PDF

    native = {id(b): i for i, b in enumerate(items)}

    ordered: list[RawBlock] = []
    band: list[RawBlock] = []
    columns = 1
    warnings: list[str] = []

    def flush() -> None:
        nonlocal columns
        if not band:
            return
        part, cols, warn = _order_band(band, native)
        ordered.extend(part)
        columns = max(columns, cols)
        if warn and warn not in warnings:
            warnings.append(warn)
        band.clear()

    for block in _y_order(items):
        width = block.bbox[2] - block.bbox[0]
        if width >= FULL_WIDTH_RATIO * page_width:
            flush()
            ordered.append(block)
        else:
            band.append(block)
    flush()
    return LayoutResult(tuple(ordered), columns, tuple(warnings))
