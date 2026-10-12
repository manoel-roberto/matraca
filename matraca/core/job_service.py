"""Orquestrador principal de processamento de ponta a ponta (PDF -> MP3).

Facade central do domínio: UIs chamam exclusivamente este serviço (RNF-01, ADR-015).
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

from matraca.config import ExtractionConfig
from matraca.core.audio_service import AudioService
from matraca.core.exceptions import (
    CancelamentoError,
    PDFInvalidoError,
)
from matraca.core.models import (
    AudioJobConfig,
    JobResult,
    NarrationText,
    PDFInfo,
)
from matraca.core.page_selection import parse_page_selection
from matraca.core.pdf_service import PDFService
from matraca.core.ports import StrategyProvider
from matraca.core.progress import (
    CancellationToken,
    ProgressCallback,
    ProgressEvent,
    Stage,
)
from matraca.core.text_pipeline import TextPipelineService
from matraca.text.normalization import NormalizationConfig

_log = logging.getLogger(__name__)


class JobService:
    """Facade central de execução de jobs do Matraca."""

    def __init__(
        self,
        pdf_service: PDFService,
        audio_service: AudioService,
        registry: StrategyProvider,
        text_pipeline: TextPipelineService | None = None,
    ) -> None:
        self.pdf_service = pdf_service
        self.audio_service = audio_service
        self.registry = registry
        self.text_pipeline = text_pipeline or TextPipelineService()

    def inspect_pdf(self, pdf_path: Path) -> PDFInfo:
        """Inspeciona o PDF e devolve metadados e total de páginas."""
        return self.pdf_service.inspect(pdf_path)

    def render_page_thumbnail(
        self,
        pdf_path: Path,
        number: int,
        *,
        max_dimension: int = 300,
    ) -> bytes:
        """Renderiza a miniatura de uma página específica de um PDF."""
        return self.pdf_service.render_page_thumbnail(pdf_path, number, max_dimension=max_dimension)

    def render_thumbnails(
        self,
        pdf_path: Path,
        pages: Sequence[int],
        *,
        max_dimension: int = 300,
    ) -> dict[int, bytes]:
        """Renderiza miniaturas para uma lista de páginas com alta eficiência."""
        return self.pdf_service.render_thumbnails(pdf_path, pages, max_dimension=max_dimension)

    def get_preview(
        self,
        pdf_path: Path,
        pages_expr: str,
        *,
        strategy_name: str = "concursos",
        extraction_config: ExtractionConfig | None = None,
        norm_config: NormalizationConfig | None = None,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> NarrationText:
        """Extrai e normaliza o texto das páginas sem gerar áudio (para prévia na UI)."""
        if cancel and cancel.is_cancelled:
            raise CancelamentoError("Prévia cancelada.")

        def emit(stage: Stage, cur: int, tot: int, msg: str) -> None:
            if progress:
                progress(ProgressEvent(stage=stage, current=cur, total=tot, message=msg))

        emit(Stage.VALIDATING, 0, 1, "Inspecionando PDF...")
        info = self.pdf_service.inspect(pdf_path)

        page_sel = parse_page_selection(pages_expr, info.page_count)
        cfg = extraction_config or ExtractionConfig()
        strat = self.registry.get(strategy_name)

        emit(
            Stage.EXTRACTING, 0, page_sel.count, f"Extraindo texto de {page_sel.count} página(s)..."
        )
        with self.pdf_service.open(pdf_path) as reader:
            extraction = strat.extract(
                reader=reader,
                pages=page_sel.pages,
                config=cfg,
                progress=progress,
                cancel=cancel,
            )

        emit(Stage.NORMALIZING, 0, len(extraction.pages), "Normalizando texto para narração...")
        pipeline = TextPipelineService(norm_config) if norm_config else self.text_pipeline
        narration = pipeline.process(extraction)

        emit(Stage.DONE, 1, 1, "Prévia gerada com sucesso.")
        return narration

    async def run_job_async(
        self,
        pdf_path: Path,
        pages_expr: str,
        audio_config: AudioJobConfig,
        *,
        strategy_name: str = "concursos",
        extraction_config: ExtractionConfig | None = None,
        norm_config: NormalizationConfig | None = None,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> JobResult:
        """Executa o pipeline completo de forma assíncrona.

        Fases: Validação -> Extração -> Normalização -> Áudio MP3.
        """
        if cancel and cancel.is_cancelled:
            raise CancelamentoError("Job cancelado antes do início.")

        def emit(stage: Stage, cur: int, tot: int, msg: str) -> None:
            if progress:
                progress(ProgressEvent(stage=stage, current=cur, total=tot, message=msg))

        emit(Stage.VALIDATING, 0, 1, "Validando arquivo PDF...")
        info = self.pdf_service.inspect(pdf_path)

        # 1. Seleção de páginas
        page_sel = parse_page_selection(pages_expr, info.page_count)

        # 2. Extração de texto
        cfg = extraction_config or ExtractionConfig()
        strat = self.registry.get(strategy_name)

        emit(
            Stage.EXTRACTING, 0, page_sel.count, f"Extraindo texto de {page_sel.count} página(s)..."
        )
        with self.pdf_service.open(pdf_path) as reader:
            extraction = strat.extract(
                reader=reader,
                pages=page_sel.pages,
                config=cfg,
                progress=progress,
                cancel=cancel,
            )

        # 3. Normalização
        emit(Stage.NORMALIZING, 0, len(extraction.pages), "Normalizando texto para fala...")
        pipeline = TextPipelineService(norm_config) if norm_config else self.text_pipeline
        narration = pipeline.process(extraction)

        if not narration.text.strip():
            raise PDFInvalidoError(
                "Nenhum texto aproveitável foi extraído das páginas selecionadas."
            )

        # 4. Síntese e gravação de áudio
        out_path, duration, size = await self.audio_service.synthesize(
            text=narration.text,
            config=audio_config,
            progress=progress,
            cancel=cancel,
        )

        all_warnings = list(extraction.warnings) + list(narration.warnings)

        return JobResult(
            output_path=out_path,
            size_bytes=size,
            estimated_duration_seconds=duration,
            warnings=tuple(all_warnings),
            stats=narration.stats,
        )

    def run_job_in_thread(
        self,
        pdf_path: Path,
        pages_expr: str,
        audio_config: AudioJobConfig,
        *,
        strategy_name: str = "concursos",
        extraction_config: ExtractionConfig | None = None,
        norm_config: NormalizationConfig | None = None,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
        on_complete: Callable[[JobResult], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> threading.Thread:
        """Executa o job completo em uma thread trabalhadora isolada.

        Garante event loop dedicado em background conforme ADR-015.
        """

        def _worker() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.run_job_async(
                        pdf_path=pdf_path,
                        pages_expr=pages_expr,
                        audio_config=audio_config,
                        strategy_name=strategy_name,
                        extraction_config=extraction_config,
                        norm_config=norm_config,
                        progress=progress,
                        cancel=cancel,
                    )
                )
                if on_complete:
                    on_complete(result)
            except Exception as exc:
                if on_error:
                    on_error(exc)
            finally:
                loop.close()

        thread = threading.Thread(target=_worker, daemon=True, name="MatracaJobWorker")
        thread.start()
        return thread
