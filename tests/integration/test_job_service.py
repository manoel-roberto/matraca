"""Testes de integração do JobService (RF-13, RNF-01, ADR-015)."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import pytest

from matraca.audio.fake_tts import FakeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.core.audio_service import AudioService
from matraca.core.exceptions import CancelamentoError, PDFSemTextoError
from matraca.core.job_service import JobService
from matraca.core.models import AudioJobConfig, CollisionPolicy, JobResult
from matraca.core.pdf_service import PDFService
from matraca.core.progress import CancellationToken, ProgressEvent
from matraca.extractors.registry import default_registry
from matraca.pdf.pymupdf_reader import PyMuPDFReader

pytestmark = pytest.mark.integration

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _make_service() -> JobService:
    pdf_service = PDFService(reader_factory=PyMuPDFReader)
    audio_service = AudioService(backend=FakeTTSBackend(), joiner=DirectMp3Joiner())
    return JobService(
        pdf_service=pdf_service,
        audio_service=audio_service,
        registry=default_registry(),
    )


def test_job_service_inspect() -> None:
    """Inspeciona metadados e contagem de páginas de um PDF real sintético."""
    service = _make_service()
    pdf_path = _FIXTURES_DIR / "texto_juridico.pdf"

    info = service.inspect_pdf(pdf_path)
    assert info.page_count >= 1
    assert not info.is_encrypted
    assert info.has_text_layer


def test_job_service_get_preview() -> None:
    """Gera prévia rápida sem sintetizar áudio."""
    service = _make_service()
    pdf_path = _FIXTURES_DIR / "texto_juridico.pdf"

    events: list[ProgressEvent] = []
    preview = service.get_preview(
        pdf_path=pdf_path,
        pages_expr="1",
        strategy_name="concursos",
        progress=events.append,
    )

    assert len(preview.original_paragraphs) >= 1
    assert len(preview.paragraphs) == len(preview.original_paragraphs)
    assert preview.stats["paragraphs"] >= 1
    assert preview.stats["words"] >= 1
    assert len(events) >= 2


def test_job_service_run_async_sucesso(tmp_path: Path) -> None:
    """Execução ponta a ponta assíncrona: PDF -> Extração -> Normalização -> MP3."""
    service = _make_service()
    pdf_path = _FIXTURES_DIR / "uma_coluna.pdf"
    out_mp3 = tmp_path / "audio_uma_coluna.mp3"

    audio_cfg = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=out_mp3,
        rate_percent=0,
        collision_policy=CollisionPolicy.RENAME,
    )

    events: list[ProgressEvent] = []
    res = asyncio.run(
        service.run_job_async(
            pdf_path=pdf_path,
            pages_expr="1",
            audio_config=audio_cfg,
            strategy_name="concursos",
            progress=events.append,
        )
    )

    assert res.output_path == out_mp3
    assert res.output_path.exists()
    assert res.size_bytes > 0
    assert res.estimated_duration_seconds > 0.0
    assert len(events) >= 5


def test_job_service_run_in_thread(tmp_path: Path) -> None:
    """Execução ponta a ponta em thread trabalhadora dedicada com callback on_complete."""
    service = _make_service()
    pdf_path = _FIXTURES_DIR / "duas_colunas.pdf"
    out_mp3 = tmp_path / "audio_duas_colunas.mp3"

    audio_cfg = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=out_mp3,
    )

    completed_result: list[JobResult] = []
    error_result: list[Exception] = []
    done_event = threading.Event()

    def _on_complete(res: JobResult) -> None:
        completed_result.append(res)
        done_event.set()

    def _on_error(exc: Exception) -> None:
        error_result.append(exc)
        done_event.set()

    thread = service.run_job_in_thread(
        pdf_path=pdf_path,
        pages_expr="1",
        audio_config=audio_cfg,
        on_complete=_on_complete,
        on_error=_on_error,
    )

    # Aguarda a conclusão da thread trabalhadora
    done = done_event.wait(timeout=10.0)
    thread.join(timeout=2.0)

    assert done, "A thread de trabalho não concluiu a tempo"
    assert not error_result, f"Ocorreu erro: {error_result}"
    assert len(completed_result) == 1
    assert completed_result[0].output_path.exists()


def test_job_service_pdf_sem_texto_lanca_erro(tmp_path: Path) -> None:
    """PDF sem texto (apenas imagem digitalizada) deve falhar com PDFSemTextoError."""
    service = _make_service()
    pdf_path = _FIXTURES_DIR / "somente_imagem.pdf"
    out_mp3 = tmp_path / "falha_imagem.mp3"

    audio_cfg = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=out_mp3,
    )

    with pytest.raises(PDFSemTextoError):
        asyncio.run(
            service.run_job_async(
                pdf_path=pdf_path,
                pages_expr="1",
                audio_config=audio_cfg,
            )
        )

    assert not out_mp3.exists()


def test_job_service_cancelamento(tmp_path: Path) -> None:
    """Cancelamento via token interrompe o job e não deixa artefatos."""
    service = _make_service()
    pdf_path = _FIXTURES_DIR / "texto_juridico.pdf"
    out_mp3 = tmp_path / "cancelado.mp3"

    audio_cfg = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=out_mp3,
    )

    token = CancellationToken()
    token.cancel()

    with pytest.raises(CancelamentoError):
        asyncio.run(
            service.run_job_async(
                pdf_path=pdf_path,
                pages_expr="1",
                audio_config=audio_cfg,
                cancel=token,
            )
        )

    assert not out_mp3.exists()
