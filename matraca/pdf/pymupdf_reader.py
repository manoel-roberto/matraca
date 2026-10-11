"""Adaptador PyMuPDF: único módulo que importa `pymupdf` (implementa `PDFReader`)."""

from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import pymupdf

from matraca.core.exceptions import PDFInvalidoError, PDFProtegidoError
from matraca.core.models import BBox, RawBlock, RawLine, RawPage

_log = logging.getLogger(__name__)

# Evita que o MuPDF escreva avisos de reparo direto no stderr; os erros são tratados por nós.
pymupdf.TOOLS.mupdf_display_errors(False)

_TEXT_FLAGS = pymupdf.TEXT_MEDIABOX_CLIP  # sem preservar ligaduras/espacos: texto mais limpo
_FULL_PAGE_IMAGE_RATIO = 0.8
_SAFE_METADATA_KEYS = ("title", "subject", "creator", "producer")


def _bbox(raw: Any) -> BBox:
    x0, y0, x1, y1 = (float(v) for v in raw)
    return (x0, y0, x1, y1)


class PyMuPDFReader:
    """Leitor de PDF baseado em PyMuPDF; use como context manager."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if not self.path.exists() or not self.path.is_file():
            raise PDFInvalidoError("O arquivo PDF não foi encontrado.", detail=f"caminho={path}")
        try:
            self._doc: Any = pymupdf.open(self.path)
        except (pymupdf.FileDataError, pymupdf.EmptyFileError, RuntimeError, ValueError) as exc:
            raise PDFInvalidoError(detail=f"{type(exc).__name__}: {exc}") from exc
        if self._doc.needs_pass:
            self._doc.close()
            raise PDFProtegidoError()
        if self._doc.page_count < 1:
            self._doc.close()
            raise PDFInvalidoError("O PDF não tem páginas.")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Fecha o documento (idempotente)."""
        if not self._doc.is_closed:
            self._doc.close()

    @property
    def page_count(self) -> int:
        return int(self._doc.page_count)

    @property
    def is_encrypted(self) -> bool:
        return bool(self._doc.is_encrypted)

    def metadata(self) -> dict[str, str]:
        meta = self._doc.metadata or {}
        return {k: str(meta[k]) for k in _SAFE_METADATA_KEYS if meta.get(k)}

    def read_page(self, number: int, *, with_tables: bool = False) -> RawPage:
        if not 1 <= number <= self.page_count:
            raise PDFInvalidoError(f"Página {number} fora do documento.")
        try:
            page = self._doc[number - 1]
            data = page.get_text("dict", flags=_TEXT_FLAGS)
            blocks = tuple(self._convert_block(b) for b in data["blocks"])
            width, height = float(page.rect.width), float(page.rect.height)
            full_image = self._has_full_page_image(page, width * height)
            tables = self._find_tables(page) if with_tables else ()
        except (RuntimeError, ValueError) as exc:
            raise PDFInvalidoError(
                f"Falha ao ler a página {number}.", detail=f"{type(exc).__name__}: {exc}"
            ) from exc
        kept = tuple(b for b in blocks if b.kind == "image" or b.lines)
        return RawPage(
            number=number,
            width=width,
            height=height,
            blocks=kept,
            table_bboxes=tables,
            has_full_page_image=full_image,
        )

    @staticmethod
    def _convert_block(block: dict[str, Any]) -> RawBlock:
        if block.get("type") == 1:
            return RawBlock(kind="image", bbox=_bbox(block["bbox"]))
        lines: list[RawLine] = []
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(str(s.get("text", "")) for s in spans)
            if not text.strip():
                continue
            lines.append(
                RawLine(
                    text=text,
                    bbox=_bbox(line["bbox"]),
                    direction=(float(line["dir"][0]), float(line["dir"][1])),
                    font_size=max(float(s.get("size", 0.0)) for s in spans),
                    color=int(spans[0].get("color", 0)),
                    alpha=min(int(s.get("alpha", 255)) for s in spans),
                    bold=any(int(s.get("flags", 0)) & 16 for s in spans),
                )
            )
        return RawBlock(kind="text", bbox=_bbox(block["bbox"]), lines=tuple(lines))

    @staticmethod
    def _has_full_page_image(page: Any, page_area: float) -> bool:
        if page_area <= 0:
            return False
        for info in page.get_image_info():
            x0, y0, x1, y1 = _bbox(info["bbox"])
            if (x1 - x0) * (y1 - y0) >= _FULL_PAGE_IMAGE_RATIO * page_area:
                return True
        return False

    @staticmethod
    def _find_tables(page: Any) -> tuple[BBox, ...]:
        try:
            finder = page.find_tables()
        except (RuntimeError, ValueError, AttributeError):
            _log.debug("find_tables indisponível ou falhou; seguindo sem tabelas")
            return ()
        return tuple(_bbox(t.bbox) for t in finder.tables)
