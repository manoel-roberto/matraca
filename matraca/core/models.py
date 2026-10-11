"""Modelos de dados imutáveis do Matraca (A.12.3).

`ProgressEvent` e `Stage` vivem em `matraca.core.progress` para evitar ciclos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal

BBox = tuple[float, float, float, float]
"""Caixa delimitadora (x0, y0, x1, y1) em pontos do PDF, origem no canto superior esquerdo."""

RATE_MIN_PERCENT = -50
RATE_MAX_PERCENT = 100


class BlockType(StrEnum):
    """Tipo semântico de um bloco extraído."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE_MARKER = "figure_marker"
    NOISE = "noise"


class CollisionPolicy(StrEnum):
    """O que fazer quando o arquivo de saída já existe."""

    ASK = "ask"
    RENAME = "rename"
    OVERWRITE = "overwrite"


@dataclass(frozen=True)
class PageSelection:
    """Seleção de páginas já validada: números 1-based, únicos e em ordem crescente."""

    expression: str
    pages: tuple[int, ...]
    total_pages: int

    def __post_init__(self) -> None:
        if self.total_pages < 1:
            raise ValueError("total_pages deve ser >= 1")
        if not self.pages:
            raise ValueError("a seleção não pode ser vazia")
        if list(self.pages) != sorted(set(self.pages)):
            raise ValueError("páginas devem ser únicas e crescentes")
        if self.pages[0] < 1 or self.pages[-1] > self.total_pages:
            raise ValueError("páginas fora do intervalo do documento")

    @classmethod
    def all(cls, total_pages: int) -> PageSelection:
        """Seleciona explicitamente todas as páginas do documento."""
        return cls(
            expression=f"1-{total_pages}",
            pages=tuple(range(1, total_pages + 1)),
            total_pages=total_pages,
        )

    @property
    def count(self) -> int:
        """Quantidade de páginas selecionadas."""
        return len(self.pages)


@dataclass(frozen=True)
class PDFInfo:
    """Informações básicas de um PDF aberto."""

    path: Path
    page_count: int
    is_encrypted: bool
    has_text_layer: bool
    metadata: dict[str, str] = field(default_factory=dict)


# --- Modelos "crus" devolvidos pelo PDFReader (sem dependência de PyMuPDF) -----------------


@dataclass(frozen=True)
class RawLine:
    """Linha de texto como lida do PDF."""

    text: str
    bbox: BBox
    direction: tuple[float, float] = (1.0, 0.0)
    font_size: float = 0.0
    color: int = 0
    alpha: int = 255
    bold: bool = False


@dataclass(frozen=True)
class RawBlock:
    """Bloco do PDF: texto (com linhas) ou imagem."""

    kind: Literal["text", "image"]
    bbox: BBox
    lines: tuple[RawLine, ...] = ()

    @property
    def text(self) -> str:
        """Texto do bloco, com uma linha por quebra."""
        return "\n".join(line.text for line in self.lines)


@dataclass(frozen=True)
class RawPage:
    """Página crua: dimensões, blocos, tabelas detectadas e indício de página digitalizada."""

    number: int
    width: float
    height: float
    blocks: tuple[RawBlock, ...]
    table_bboxes: tuple[BBox, ...] = ()
    has_full_page_image: bool = False

    @property
    def has_text(self) -> bool:
        """Indica se há algum texto não vazio na página."""
        return any(b.kind == "text" and b.text.strip() for b in self.blocks)


# --- Resultado da extração -----------------------------------------------------------------


@dataclass(frozen=True)
class ExtractedBlock:
    """Bloco de texto extraído, já classificado."""

    text: str
    page: int
    bbox: BBox
    block_type: BlockType = BlockType.PARAGRAPH
    confidence: float | None = None


@dataclass(frozen=True)
class ExtractedPage:
    """Página extraída."""

    number: int
    blocks: tuple[ExtractedBlock, ...]
    warnings: tuple[str, ...] = ()
    empty: bool = False


@dataclass(frozen=True)
class NoiseRecord:
    """Registro explicável de um bloco removido como ruído (sem texto integral)."""

    page: int
    reason: str
    signals: tuple[str, ...]
    snippet: str  # trecho curto/truncado, nunca o texto integral


@dataclass(frozen=True)
class ExtractionResult:
    """Resultado completo da extração."""

    pages: tuple[ExtractedPage, ...]
    strategy_name: str
    stats: dict[str, int] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    noise_records: tuple[NoiseRecord, ...] = ()

    @property
    def total_chars(self) -> int:
        """Total de caracteres de todos os blocos."""
        return sum(len(b.text) for p in self.pages for b in p.blocks)


# --- Normalização e áudio ------------------------------------------------------------------


@dataclass(frozen=True)
class NarrationText:
    """Texto normalizado para narração, alinhado 1:1 com o original por parágrafo."""

    paragraphs: tuple[str, ...]
    original_paragraphs: tuple[str, ...]
    stats: dict[str, int] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.paragraphs) != len(self.original_paragraphs):
            raise ValueError("parágrafos normalizados e originais devem estar alinhados")

    @property
    def text(self) -> str:
        """Texto normalizado completo, parágrafos separados por linha em branco."""
        return "\n\n".join(self.paragraphs)

    @property
    def original_text(self) -> str:
        """Texto original completo, parágrafos separados por linha em branco."""
        return "\n\n".join(self.original_paragraphs)


@dataclass(frozen=True)
class VoiceInfo:
    """Voz de síntese; só campos que o serviço fornece."""

    short_name: str
    locale: str
    gender: str | None = None
    friendly_name: str | None = None


@dataclass(frozen=True)
class AudioJobConfig:
    """Configuração de uma geração de áudio."""

    voice: str
    output_path: Path
    rate_percent: int = 0
    collision_policy: CollisionPolicy = CollisionPolicy.ASK

    def __post_init__(self) -> None:
        if not RATE_MIN_PERCENT <= self.rate_percent <= RATE_MAX_PERCENT:
            raise ValueError(
                f"rate_percent deve estar entre {RATE_MIN_PERCENT} e {RATE_MAX_PERCENT}"
            )
        if not self.voice.strip():
            raise ValueError("voz não pode ser vazia")


@dataclass(frozen=True)
class JobResult:
    """Resultado final de um trabalho PDF → MP3."""

    output_path: Path
    size_bytes: int
    estimated_duration_seconds: float
    warnings: tuple[str, ...] = ()
    stats: dict[str, int] = field(default_factory=dict)
