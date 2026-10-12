"""Testes unitários do DesktopPresenter com FakeView sem display (RF-15, A.13.6)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from matraca.audio.fake_tts import FakeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.core.audio_service import AudioService
from matraca.core.job_service import JobService
from matraca.core.models import CollisionPolicy, JobResult, NarrationText, PDFInfo, VoiceInfo
from matraca.core.pdf_service import PDFService
from matraca.extractors.registry import default_registry
from matraca.gui.presenter import DesktopPresenter, UIState
from matraca.pdf.pymupdf_reader import PyMuPDFReader

pytestmark = pytest.mark.unit

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class FakeDesktopView:
    """Implementação simulada da View em memória para testes sem display."""

    def __init__(self) -> None:
        self.states: list[UIState] = []
        self.pdf_info: PDFInfo | None = None
        self.voices: list[VoiceInfo] = []
        self.default_voice: str = ""
        self.progresses: list[tuple[float, str]] = []
        self.preview_result: NarrationText | None = None
        self.success_result: JobResult | None = None
        self.error_messages: list[str] = []
        self.output_path: Path | None = None
        self.thumbnails: list[tuple[int, bytes]] | None = None
        self.total_selected: int = 0

    def set_state(self, state: UIState) -> None:
        self.states.append(state)

    def set_pdf_info(self, info: PDFInfo) -> None:
        self.pdf_info = info

    def set_voices(self, voices: list[VoiceInfo], default_short_name: str) -> None:
        self.voices = voices
        self.default_voice = default_short_name

    def set_progress(self, fraction: float, message: str) -> None:
        self.progresses.append((fraction, message))

    def show_preview(self, preview: NarrationText) -> None:
        self.preview_result = preview

    def show_thumbnails(
        self,
        thumbnails: list[tuple[int, bytes]],
        total_selected: int,
    ) -> None:
        self.thumbnails = thumbnails
        self.total_selected = total_selected

    def show_success(self, result: JobResult) -> None:
        self.success_result = result

    def show_error(self, message: str) -> None:
        self.error_messages.append(message)

    def set_output_path(self, path: Path) -> None:
        self.output_path = path


def _make_presenter() -> tuple[DesktopPresenter, FakeDesktopView]:
    view = FakeDesktopView()
    pdf_service = PDFService(reader_factory=PyMuPDFReader)
    audio_service = AudioService(backend=FakeTTSBackend(), joiner=DirectMp3Joiner())
    job_service = JobService(
        pdf_service=pdf_service,
        audio_service=audio_service,
        registry=default_registry(),
    )
    presenter = DesktopPresenter(view=view, job_service=job_service)
    return presenter, view


def test_presenter_init_voices() -> None:
    """Inicialização de vozes carrega lista na View."""
    presenter, view = _make_presenter()
    presenter.init_voices()

    assert len(view.voices) >= 1
    assert view.default_voice == "pt-BR-AntonioNeural"


def test_presenter_on_pdf_selected_sucesso() -> None:
    """Seleção de PDF válido atualiza metadados e sugere caminho de saída."""
    presenter, view = _make_presenter()
    pdf_path = _FIXTURES_DIR / "uma_coluna.pdf"

    presenter.on_pdf_selected(pdf_path)

    assert view.pdf_info is not None
    assert view.pdf_info.page_count >= 1
    assert view.output_path == pdf_path.with_suffix(".mp3")
    assert UIState.IDLE in view.states


def test_presenter_on_pdf_selected_erro() -> None:
    """Seleção de PDF corrompido emite mensagem de erro e muda estado para ERROR."""
    presenter, view = _make_presenter()
    pdf_path = _FIXTURES_DIR / "corrompido.pdf"

    presenter.on_pdf_selected(pdf_path)

    assert len(view.error_messages) >= 1
    assert UIState.ERROR in view.states


def test_presenter_preview_sucesso() -> None:
    """Geração de prévia roda em background e devolve resultado para a View."""
    presenter, view = _make_presenter()
    pdf_path = _FIXTURES_DIR / "texto_juridico.pdf"
    presenter.on_pdf_selected(pdf_path)

    presenter.on_preview_requested(pages_expr="1", strategy_name="concursos")

    # Aguarda a thread de preview colocar o evento na fila
    for _ in range(50):
        presenter.poll_events()
        if view.preview_result is not None:
            break
        time.sleep(0.02)

    assert view.preview_result is not None
    assert len(view.preview_result.paragraphs) >= 1


def test_presenter_preview_sem_pdf() -> None:
    """Tentar gerar prévia sem selecionar PDF exibe erro imediatamente."""
    presenter, view = _make_presenter()
    presenter.on_preview_requested(pages_expr="1")

    assert len(view.error_messages) == 1
    assert "Selecione um PDF" in view.error_messages[0]


def test_presenter_start_job_sucesso(tmp_path: Path) -> None:
    """Execução completa do job via presenter atualiza progresso e finaliza com show_success."""
    presenter, view = _make_presenter()
    pdf_path = _FIXTURES_DIR / "uma_coluna.pdf"
    presenter.on_pdf_selected(pdf_path)

    out_mp3 = tmp_path / "saida_desktop.mp3"
    presenter.on_start_requested(
        pages_expr="1",
        voice="pt-BR-AntonioNeural",
        rate_percent=0,
        out_path=out_mp3,
        strategy_name="concursos",
        collision_policy=CollisionPolicy.RENAME,
    )

    # Aguarda a thread de trabalho finalizar e despachar os eventos
    for _ in range(100):
        presenter.poll_events()
        if view.success_result is not None:
            break
        time.sleep(0.05)

    assert view.success_result is not None
    assert view.success_result.output_path.exists()
    assert UIState.DONE in view.states
    assert len(view.progresses) >= 3


def test_presenter_cancelamento(tmp_path: Path) -> None:
    """Cancelamento solicitado pelo usuário interrompe o job e atualiza o estado."""
    presenter, view = _make_presenter()
    pdf_path = _FIXTURES_DIR / "texto_juridico.pdf"
    presenter.on_pdf_selected(pdf_path)

    out_mp3 = tmp_path / "cancelado.mp3"
    presenter.on_start_requested(
        pages_expr="1",
        voice="pt-BR-AntonioNeural",
        rate_percent=0,
        out_path=out_mp3,
    )

    # Dispara cancelamento logo em seguida
    presenter.on_cancel_requested()

    assert UIState.CANCELLED in view.states


def test_presenter_nova_tentativa_apos_falha(tmp_path: Path) -> None:
    """Após um erro, é possível selecionar outro PDF e reiniciar normalmente."""
    presenter, view = _make_presenter()

    # 1. Falha inicial com PDF corrompido
    presenter.on_pdf_selected(_FIXTURES_DIR / "corrompido.pdf")
    assert UIState.ERROR in view.states

    # 2. Nova tentativa com PDF válido
    pdf_valido = _FIXTURES_DIR / "uma_coluna.pdf"
    presenter.on_pdf_selected(pdf_valido)
    assert view.pdf_info is not None
    assert UIState.IDLE in view.states

    # 3. Execução bem sucedida
    out_mp3 = tmp_path / "recuperado.mp3"
    presenter.on_start_requested(
        pages_expr="1",
        voice="pt-BR-AntonioNeural",
        rate_percent=0,
        out_path=out_mp3,
    )

    for _ in range(100):
        presenter.poll_events()
        if view.success_result is not None:
            break
        time.sleep(0.05)

    assert view.success_result is not None
    assert UIState.DONE in view.states


def test_presenter_visualize_pages_sucesso() -> None:
    presenter, view = _make_presenter()
    pdf_valido = _FIXTURES_DIR / "uma_coluna.pdf"
    presenter.on_pdf_selected(pdf_valido)

    presenter.on_visualize_pages_requested("1-2")

    for _ in range(60):
        presenter.poll_events()
        if view.thumbnails is not None:
            break
        time.sleep(0.05)

    assert view.thumbnails is not None
    assert len(view.thumbnails) == 2
    assert view.total_selected == 2
    assert view.thumbnails[0][0] == 1
    assert view.thumbnails[1][0] == 2
    assert isinstance(view.thumbnails[0][1], bytes)
    assert view.thumbnails[0][1].startswith(b"\x89PNG\r\n\x1a\n")


def test_presenter_visualize_pages_sem_pdf_erro() -> None:
    presenter, view = _make_presenter()
    presenter.on_visualize_pages_requested("1")
    assert len(view.error_messages) == 1
    assert "Selecione um arquivo PDF" in view.error_messages[0]


def test_presenter_visualize_pages_limita_max_thumbnails() -> None:
    presenter, view = _make_presenter()
    pdf_valido = _FIXTURES_DIR / "uma_coluna.pdf"  # tem 3 páginas
    presenter.on_pdf_selected(pdf_valido)

    presenter.on_visualize_pages_requested("1-3", max_thumbnails=2)

    for _ in range(60):
        presenter.poll_events()
        if view.thumbnails is not None:
            break
        time.sleep(0.05)

    assert view.thumbnails is not None
    assert len(view.thumbnails) == 2
    assert view.total_selected == 3
