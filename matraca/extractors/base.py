"""Base comum das estratégias de extração (A.12.5).

Reexporta os contratos de `core.ports` e implementa o fluxo compartilhado:
amostragem para perfil de ruído → leitura incremental página a página → descarte de ruído →
tabelas/figuras → ordem de leitura → classificação de blocos → avisos agregados.
"""

from __future__ import annotations

import re
import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field

from matraca.config import ExtractionConfig
from matraca.core.exceptions import PDFSemTextoError
from matraca.core.models import (
    BBox,
    BlockType,
    ExtractedBlock,
    ExtractedPage,
    ExtractionResult,
    NoiseRecord,
    RawBlock,
    RawLine,
    RawPage,
)
from matraca.core.pdf_service import sample_indices
from matraca.core.ports import PDFReader, PDFTextStrategy
from matraca.core.progress import CancellationToken, ProgressCallback, ProgressEvent, Stage
from matraca.extractors.layout import order_blocks
from matraca.extractors.noise import NoiseDetector, NoisePattern, make_record

__all__ = ["BaseExtractor", "PDFTextStrategy"]

TABLE_MARKER = "[Tabela nesta página]"
FIGURE_MARKER = "[Figura nesta página]"
_MIN_FIGURE_AREA_RATIO = 0.02
_HEADING_SIZE_RATIO = 1.15
_HEADING_MAX_CHARS = 150
_LIST_ITEM = re.compile(r"^\s*(?:[-•●▪◦]|\(?[A-Za-z]\)|\(?[IVXLCDM]+\)?\s*[-–—]|\d{1,3}[.)])\s+")


def _center(bbox: BBox) -> tuple[float, float]:
    return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2


def _inside(point: tuple[float, float], bbox: BBox) -> bool:
    return bbox[0] <= point[0] <= bbox[2] and bbox[1] <= point[1] <= bbox[3]


def _marker_block(text: str, bbox: BBox) -> RawBlock:
    return RawBlock(kind="text", bbox=bbox, lines=(RawLine(text=text, bbox=bbox),))


@dataclass
class _Run:
    """Estado mutável de UMA execução de extração (nunca compartilhado entre execuções)."""

    owner: BaseExtractor
    config: ExtractionConfig
    detector: NoiseDetector
    stats: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    noise: list[NoiseRecord] = field(default_factory=list)
    pages_with_text: int = 0

    def bump(self, key: str, amount: int = 1) -> None:
        self.stats[key] = self.stats.get(key, 0) + amount

    def process_page(self, raw: RawPage) -> ExtractedPage:
        page_warnings: list[str] = []
        text_blocks = [b for b in raw.blocks if b.kind == "text" and b.text.strip()]
        if text_blocks:
            self.pages_with_text += 1
        else:
            page_warnings.append(self._empty_page_warning(raw))
            self.bump("empty_pages")
            return ExtractedPage(raw.number, (), tuple(page_warnings), empty=True)

        kept = self._drop_noise(raw, text_blocks)
        markers: dict[int, BlockType] = {}
        kept = self._apply_tables(raw, kept, markers)
        kept = self._apply_figures(raw, kept, markers)

        layout = order_blocks(kept, raw.width, detect_columns=self.config.detect_columns)
        page_warnings.extend(layout.warnings)
        median = self._median_font(layout.blocks)
        blocks = tuple(
            ExtractedBlock(
                text=self.owner.transform_block(b.text.strip()) if id(b) not in markers else b.text,
                page=raw.number,
                bbox=b.bbox,
                block_type=markers.get(id(b)) or self._classify(b, median),
            )
            for b in layout.blocks
        )
        self.bump("blocks", len(blocks))
        self.bump("chars", sum(len(b.text) for b in blocks))
        return ExtractedPage(raw.number, blocks, tuple(page_warnings), empty=not blocks)

    @staticmethod
    def _empty_page_warning(raw: RawPage) -> str:
        if raw.has_full_page_image:
            return (
                f"Página {raw.number}: possível página digitalizada "
                "(sem texto; OCR não suportado nesta versão)."
            )
        return f"Página {raw.number}: sem texto."

    def _drop_noise(self, raw: RawPage, blocks: list[RawBlock]) -> list[RawBlock]:
        if not self.config.remove_headers_footers:
            return blocks
        kept: list[RawBlock] = []
        for block in blocks:
            decision = self.detector.classify(raw, block)
            if decision is None:
                kept.append(block)
                continue
            self.bump(f"ruido_{decision.reason}")
            self.noise.append(make_record(raw.number, decision, block.text))
        return kept

    def _apply_tables(
        self, raw: RawPage, blocks: list[RawBlock], markers: dict[int, BlockType]
    ) -> list[RawBlock]:
        if self.config.tables == "linear" or not raw.table_bboxes:
            return blocks
        self.bump("tabelas", len(raw.table_bboxes))
        remaining = [
            b for b in blocks if not any(_inside(_center(b.bbox), t) for t in raw.table_bboxes)
        ]
        if self.config.tables == "marker":
            for table in raw.table_bboxes:
                marker = _marker_block(TABLE_MARKER, table)
                markers[id(marker)] = BlockType.TABLE
                remaining.append(marker)
        return remaining

    def _apply_figures(
        self, raw: RawPage, blocks: list[RawBlock], markers: dict[int, BlockType]
    ) -> list[RawBlock]:
        page_area = raw.width * raw.height
        figures = [
            b
            for b in raw.blocks
            if b.kind == "image"
            and not raw.has_full_page_image
            and page_area > 0
            and (b.bbox[2] - b.bbox[0]) * (b.bbox[3] - b.bbox[1])
            >= _MIN_FIGURE_AREA_RATIO * page_area
        ]
        if not figures:
            return blocks
        self.bump("figuras", len(figures))
        if self.config.figures == "marker":
            for fig in figures:
                marker = _marker_block(FIGURE_MARKER, fig.bbox)
                markers[id(marker)] = BlockType.FIGURE_MARKER
                blocks = [*blocks, marker]
        return blocks

    @staticmethod
    def _median_font(blocks: Sequence[RawBlock]) -> float:
        sizes = [line.font_size for b in blocks for line in b.lines if line.font_size > 0]
        return statistics.median(sizes) if sizes else 0.0

    @staticmethod
    def _classify(block: RawBlock, median_size: float) -> BlockType:
        text = block.text.strip()
        if _LIST_ITEM.match(text):
            return BlockType.LIST_ITEM
        largest = max((line.font_size for line in block.lines), default=0.0)
        short = len(text) <= _HEADING_MAX_CHARS and len(block.lines) <= 3
        bigger = median_size > 0 and largest >= _HEADING_SIZE_RATIO * median_size
        all_bold = bool(block.lines) and all(line.bold for line in block.lines)
        if short and not text.endswith(".") and (bigger or all_bold):
            return BlockType.HEADING
        return BlockType.PARAGRAPH

    def final_warnings(self) -> tuple[str, ...]:
        out = list(self.warnings)
        for key, singular, plural, mode in (
            ("tabelas", "tabela", "tabelas", self.config.tables),
            ("figuras", "figura", "figuras", self.config.figures),
        ):
            n = self.stats.get(key, 0)
            if n and mode == "ignore":
                out.append(f"{n} {singular if n == 1 else plural} não foi(ram) lida(s).")
            elif n and mode == "marker":
                out.append(
                    f"{n} {singular if n == 1 else plural} substituída(s) por marcador no texto."
                )
        removed = sum(v for k, v in self.stats.items() if k.startswith("ruido_"))
        if removed:
            out.append(f"{removed} bloco(s) de cabeçalho/rodapé/marca removido(s) como ruído.")
        return tuple(out)


class BaseExtractor:
    """Implementação base de `PDFTextStrategy`; subclasses definem nome, padrões e ajustes."""

    name: str = "base"
    display_name: str = "Base"
    implemented: bool = True
    noise_patterns: tuple[NoisePattern, ...] = ()

    def transform_block(self, text: str) -> str:
        """Ajuste específico da estratégia ao texto de um bloco (padrão: nenhum)."""
        return text

    def extract(
        self,
        reader: PDFReader,
        pages: Sequence[int],
        config: ExtractionConfig,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> ExtractionResult:
        """Extrai as páginas `pages` (na ordem dada), página a página."""
        detector = NoiseDetector(config, self.noise_patterns)
        run = _Run(owner=self, config=config, detector=detector)

        if config.remove_headers_footers:
            sample = [
                reader.read_page(n)
                for n in self._sample(pages, config.sample_pages)
                if not (cancel and cancel.is_cancelled)
            ]
            detector.fit(sample)

        total = len(pages)
        extracted: list[ExtractedPage] = []
        for index, number in enumerate(pages, start=1):
            if cancel is not None:
                cancel.raise_if_cancelled()
            if progress is not None:
                progress(ProgressEvent(Stage.EXTRACTING, index, total, f"Página {number}"))
            raw = reader.read_page(number, with_tables=config.tables != "linear")
            page = run.process_page(raw)
            extracted.append(page)

        if run.pages_with_text == 0:
            raise PDFSemTextoError()
        run.stats["pages"] = total
        warnings = [w for p in extracted for w in p.warnings] + list(run.final_warnings())
        return ExtractionResult(
            pages=tuple(extracted),
            strategy_name=self.name,
            stats=dict(run.stats),
            warnings=tuple(warnings),
            noise_records=tuple(run.noise),
        )

    @staticmethod
    def _sample(pages: Sequence[int], limit: int) -> list[int]:
        """Amostra distribuída das páginas selecionadas para o perfil de ruído."""
        positions = sample_indices(len(pages), limit)
        return [pages[p - 1] for p in positions]
