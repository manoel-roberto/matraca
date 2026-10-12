"""Presenter da interface Desktop seguindo o padrão MVP (RF-15, A.13.6).

Isolado de qualquer framework visual (sem customtkinter), testável sem display.
Comunicação thread-safe do worker para a UI via queue.Queue.
"""

from __future__ import annotations

import logging
import queue
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple, Protocol

from matraca.core.exceptions import MatracaError
from matraca.core.job_service import JobService
from matraca.core.models import (
    AudioJobConfig,
    CollisionPolicy,
    JobResult,
    NarrationText,
    PDFInfo,
    VoiceInfo,
)
from matraca.core.page_selection import parse_page_selection
from matraca.core.progress import CancellationToken, ProgressEvent, Stage
from matraca.utils.paths import resolve_collision, validate_output_path

_log = logging.getLogger(__name__)


class UIState(StrEnum):
    """Estados operacionais da interface gráfica."""

    IDLE = "idle"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    NORMALIZING = "normalizing"
    SYNTHESIZING = "synthesizing"
    FINALIZING = "finalizing"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


class DesktopView(Protocol):
    """Contrato que a View (janela gráfica) deve implementar."""

    def set_state(self, state: UIState) -> None: ...

    def set_pdf_info(self, info: PDFInfo) -> None: ...

    def set_voices(self, voices: list[VoiceInfo], default_short_name: str) -> None: ...

    def set_progress(self, fraction: float, message: str) -> None: ...

    def show_preview(self, preview: NarrationText) -> None: ...

    def show_thumbnails(
        self,
        thumbnails: list[tuple[int, bytes]],
        total_selected: int,
    ) -> None: ...

    def show_success(self, result: JobResult) -> None: ...

    def show_error(self, message: str) -> None: ...

    def set_output_path(self, path: Path) -> None: ...


class UIEvent(NamedTuple):
    type: str
    data: object = None


class DesktopPresenter:
    """Presenter que orquestra a lógica de apresentação e tarefas de background."""

    def __init__(self, view: DesktopView, job_service: JobService) -> None:
        self.view = view
        self.job_service = job_service
        self.events_queue: queue.Queue[UIEvent] = queue.Queue()

        self.current_pdf: Path | None = None
        self.pdf_info: PDFInfo | None = None
        self.cancel_token: CancellationToken | None = None
        self.state: UIState = UIState.IDLE

    def init_voices(self, default_locale: str = "pt-BR") -> None:
        """Carrega lista de vozes disponíveis."""
        try:
            import asyncio

            voices_list = asyncio.run(
                self.job_service.audio_service.backend.list_voices(default_locale)
            )
            default_voice = voices_list[0].short_name if voices_list else "pt-BR-AntonioNeural"
            self.view.set_voices(voices_list, default_voice)
        except Exception:
            # Fallback seguro com vozes pt-BR padrão conhecidas
            fallback = [
                VoiceInfo(
                    short_name="pt-BR-AntonioNeural",
                    locale="pt-BR",
                    gender="Male",
                    friendly_name="Antonio (pt-BR)",
                ),
                VoiceInfo(
                    short_name="pt-BR-FranciscaNeural",
                    locale="pt-BR",
                    gender="Female",
                    friendly_name="Francisca (pt-BR)",
                ),
            ]
            self.view.set_voices(fallback, "pt-BR-AntonioNeural")

    def on_pdf_selected(self, pdf_path: Path) -> None:
        """Chamado quando o usuário seleciona um novo arquivo PDF."""
        self.current_pdf = pdf_path
        self._set_state(UIState.VALIDATING)
        self.view.set_progress(0.0, "Inspecionando PDF...")

        try:
            info = self.job_service.inspect_pdf(pdf_path)
            self.pdf_info = info
            self.view.set_pdf_info(info)
            suggested_out = pdf_path.with_suffix(".mp3")
            self.view.set_output_path(suggested_out)
            self._set_state(UIState.IDLE)
            self.view.set_progress(1.0, f"PDF carregado: {info.page_count} página(s).")
        except MatracaError as exc:
            self._set_state(UIState.ERROR)
            self.view.show_error(exc.user_message)
        except Exception as exc:
            self._set_state(UIState.ERROR)
            self.view.show_error(f"Erro ao abrir PDF: {exc}")

    def on_preview_requested(
        self,
        pages_expr: str,
        strategy_name: str = "concursos",
    ) -> None:
        """Solicita a geração de prévia do texto em background."""
        if not self.current_pdf:
            self.view.show_error("Selecione um PDF antes de gerar a prévia.")
            return

        self._set_state(UIState.EXTRACTING)
        self.view.set_progress(0.0, "Gerando prévia do texto...")
        pdf_path = self.current_pdf

        def _worker() -> None:
            try:

                def _prog(ev: ProgressEvent) -> None:
                    self.events_queue.put(UIEvent("progress", ev))

                preview = self.job_service.get_preview(
                    pdf_path=pdf_path,
                    pages_expr=pages_expr,
                    strategy_name=strategy_name,
                    progress=_prog,
                )
                self.events_queue.put(UIEvent("preview_done", preview))
            except MatracaError as exc:
                self.events_queue.put(UIEvent("error", exc.user_message))
            except Exception as exc:
                self.events_queue.put(UIEvent("error", f"Falha na prévia: {exc}"))

        import threading

        t = threading.Thread(target=_worker, daemon=True, name="PreviewWorker")
        t.start()

    def on_visualize_pages_requested(self, pages_expr: str, max_thumbnails: int = 20) -> None:
        """Solicita a renderização de miniaturas das páginas selecionadas em background."""
        if not self.current_pdf:
            self.view.show_error("Selecione um arquivo PDF antes de visualizar as páginas.")
            return

        if not self.pdf_info:
            try:
                self.pdf_info = self.job_service.inspect_pdf(self.current_pdf)
            except Exception as exc:
                self.view.show_error(f"Não foi possível inspecionar o PDF: {exc}")
                return

        try:
            page_sel = parse_page_selection(pages_expr, self.pdf_info.page_count)
        except MatracaError as exc:
            self.view.show_error(exc.user_message)
            return
        except Exception as exc:
            self.view.show_error(f"Seleção de páginas inválida: {exc}")
            return

        total_selected = page_sel.count
        pages_to_render = list(page_sel.pages[:max_thumbnails])
        pdf_path = self.current_pdf

        self.view.set_progress(
            0.0, f"Renderizando miniaturas de {len(pages_to_render)} página(s)..."
        )

        def _worker() -> None:
            try:
                thumbs = self.job_service.render_thumbnails(
                    pdf_path, pages_to_render, max_dimension=250
                )
                result_list = [(p, thumbs[p]) for p in pages_to_render if p in thumbs]
                self.events_queue.put(UIEvent("thumbnails", (result_list, total_selected)))
            except MatracaError as exc:
                self.events_queue.put(UIEvent("error", exc.user_message))
            except Exception as exc:
                self.events_queue.put(UIEvent("error", f"Falha ao gerar miniaturas: {exc}"))

        import threading

        t = threading.Thread(target=_worker, daemon=True, name="ThumbnailWorker")
        t.start()

    def on_start_requested(
        self,
        pages_expr: str,
        voice: str,
        rate_percent: int,
        out_path: Path,
        strategy_name: str = "concursos",
        collision_policy: CollisionPolicy = CollisionPolicy.RENAME,
    ) -> None:
        """Inicia o processamento completo PDF -> MP3."""
        if not self.current_pdf:
            self.view.show_error("Selecione um arquivo PDF de entrada.")
            return

        try:
            validated_out = validate_output_path(out_path, source_pdf=self.current_pdf)
            final_out = resolve_collision(validated_out, collision_policy)
        except MatracaError as exc:
            self.view.show_error(exc.user_message)
            return
        except Exception as exc:
            self.view.show_error(f"Caminho de saída inválido: {exc}")
            return

        audio_cfg = AudioJobConfig(
            voice=voice,
            output_path=final_out,
            rate_percent=rate_percent,
            collision_policy=collision_policy,
        )

        self.cancel_token = CancellationToken()
        self._set_state(UIState.EXTRACTING)
        self.view.set_progress(0.0, "Iniciando processamento...")

        def _prog(ev: ProgressEvent) -> None:
            self.events_queue.put(UIEvent("progress", ev))

        def _complete(result: JobResult) -> None:
            self.events_queue.put(UIEvent("job_done", result))

        def _error(exc: Exception) -> None:
            msg = exc.user_message if isinstance(exc, MatracaError) else str(exc)
            self.events_queue.put(UIEvent("error", msg))

        self.job_service.run_job_in_thread(
            pdf_path=self.current_pdf,
            pages_expr=pages_expr,
            audio_config=audio_cfg,
            strategy_name=strategy_name,
            progress=_prog,
            cancel=self.cancel_token,
            on_complete=_complete,
            on_error=_error,
        )

    def on_cancel_requested(self) -> None:
        """Solicita o cancelamento imediato da tarefa em execução."""
        if self.cancel_token:
            self.cancel_token.cancel()
            self._set_state(UIState.CANCELLED)
            self.view.set_progress(0.0, "Operação cancelada pelo usuário.")

    def poll_events(self) -> None:
        """Processa eventos acumulados na fila (chamado na thread da UI via after())."""
        while not self.events_queue.empty():
            try:
                ev = self.events_queue.get_nowait()
            except queue.Empty:
                break

            if ev.type == "progress":
                prog = ev.data
                if isinstance(prog, ProgressEvent):
                    self.view.set_progress(prog.fraction, prog.message)
                    stage_map = {
                        Stage.VALIDATING: UIState.VALIDATING,
                        Stage.EXTRACTING: UIState.EXTRACTING,
                        Stage.NORMALIZING: UIState.NORMALIZING,
                        Stage.SYNTHESIZING: UIState.SYNTHESIZING,
                        Stage.FINALIZING: UIState.FINALIZING,
                        Stage.DONE: UIState.DONE,
                        Stage.ERROR: UIState.ERROR,
                        Stage.CANCELLED: UIState.CANCELLED,
                    }
                    if prog.stage in stage_map:
                        self._set_state(stage_map[prog.stage])

            elif ev.type == "preview_done":
                if isinstance(ev.data, NarrationText):
                    self._set_state(UIState.IDLE)
                    self.view.show_preview(ev.data)

            elif ev.type == "thumbnails":
                if isinstance(ev.data, tuple) and len(ev.data) == 2:
                    thumbs_list, total = ev.data
                    msg = f"Miniaturas geradas ({len(thumbs_list)} exibidas)."
                    self.view.set_progress(1.0, msg)
                    self.view.show_thumbnails(thumbs_list, total)

            elif ev.type == "job_done":
                if isinstance(ev.data, JobResult):
                    self._set_state(UIState.DONE)
                    self.view.show_success(ev.data)

            elif ev.type == "error":
                self._set_state(UIState.ERROR)
                self.view.show_error(str(ev.data))

    def _set_state(self, new_state: UIState) -> None:
        self.state = new_state
        self.view.set_state(new_state)
