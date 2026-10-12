"""Serviço de PDF: abre/valida via `PDFReader` injetado (RF-01, RF-02, RF-08)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from matraca.core.exceptions import PDFInvalidoError
from matraca.core.models import PDFInfo
from matraca.core.ports import PDFReader, PDFReaderFactory

_TEXT_SAMPLE_PAGES = 8


def sample_indices(total: int, count: int) -> list[int]:
    """`count` números de página (1-based) distribuídos uniformemente em [1, total]."""
    if total <= count:
        return list(range(1, total + 1))
    step = (total - 1) / (count - 1) if count > 1 else 0
    return sorted({1 + round(i * step) for i in range(count)})


class PDFService:
    """Abre PDFs e extrai informações básicas; não conhece PyMuPDF."""

    def __init__(self, reader_factory: PDFReaderFactory) -> None:
        self._factory = reader_factory

    def open(self, path: Path) -> PDFReader:
        """Abre o PDF (o chamador deve usá-lo como context manager e fechá-lo)."""
        if path.exists() and path.is_file() and path.stat().st_size == 0:
            raise PDFInvalidoError("O arquivo PDF está vazio.", detail=f"caminho={path}")
        return self._factory(path)

    def inspect(self, path: Path) -> PDFInfo:
        """Abre, amostra algumas páginas para estimar a camada de texto e fecha o arquivo."""
        with self.open(path) as reader:
            has_text = any(
                reader.read_page(n).has_text
                for n in sample_indices(reader.page_count, _TEXT_SAMPLE_PAGES)
            )
            return PDFInfo(
                path=path,
                page_count=reader.page_count,
                is_encrypted=reader.is_encrypted,
                has_text_layer=has_text,
                metadata=reader.metadata(),
            )

    def render_page_thumbnail(self, path: Path, number: int, *, max_dimension: int = 300) -> bytes:
        """Renderiza a miniatura de uma página específica de um PDF."""
        with self.open(path) as reader:
            return reader.render_page_thumbnail(number, max_dimension=max_dimension)

    def render_thumbnails(
        self,
        path: Path,
        pages: Sequence[int],
        *,
        max_dimension: int = 300,
    ) -> dict[int, bytes]:
        """Renderiza miniaturas para uma sequência de páginas abrindo o documento uma única vez."""
        with self.open(path) as reader:
            return {
                num: reader.render_page_thumbnail(num, max_dimension=max_dimension) for num in pages
            }
