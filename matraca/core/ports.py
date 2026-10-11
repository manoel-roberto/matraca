"""Contratos (Protocols) implementados pelos adaptadores (A.12.5 e A.12.6).

`core/` depende apenas destes contratos, nunca de PyMuPDF, edge-tts ou toolkits de UI.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from matraca.config import ExtractionConfig
from matraca.core.models import ExtractionResult, RawPage, VoiceInfo
from matraca.core.progress import CancellationToken, ProgressCallback


class PDFReader(Protocol):
    """Leitor de um PDF aberto. Deve ser usado como context manager (fecha o arquivo)."""

    path: Path

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @property
    def page_count(self) -> int:
        """Total de páginas do documento."""
        ...

    @property
    def is_encrypted(self) -> bool:
        """Indica se o documento é protegido por senha."""
        ...

    def metadata(self) -> dict[str, str]:
        """Metadados seguros (título, autor...), sem dados pessoais sensíveis."""
        ...

    def read_page(self, number: int, *, with_tables: bool = False) -> RawPage:
        """Lê uma página (1-based) sob demanda; detecta tabelas apenas se `with_tables`."""
        ...


PDFReaderFactory = Callable[[Path], PDFReader]
"""Abre um PDF; lança `PDFInvalidoError`/`PDFProtegidoError` quando apropriado."""


@runtime_checkable
class PDFTextStrategy(Protocol):
    """Estratégia de extração de texto (Strategy). Não conhece widgets nem UI."""

    name: str
    display_name: str
    implemented: bool

    def extract(
        self,
        reader: PDFReader,
        pages: Sequence[int],
        config: ExtractionConfig,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> ExtractionResult: ...


class TTSBackend(Protocol):
    """Backend de síntese de fala injetável."""

    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]: ...

    async def synthesize_to_file(
        self,
        text: str,
        voice: str,
        rate: str,
        dest: Path,
        cancel: CancellationToken | None,
    ) -> None: ...
