"""Testes unitários do AudioService (RF-11 a RF-14, RF-17, A.13.5)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from matraca.audio.fake_tts import FakeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.core.audio_service import AudioService, format_rate
from matraca.core.exceptions import (
    CancelamentoError,
    SaidaInvalidaError,
    TTSErroDeRedeError,
)
from matraca.core.models import AudioJobConfig, CollisionPolicy
from matraca.core.progress import CancellationToken, ProgressEvent
from matraca.utils.paths import resolve_collision

pytestmark = pytest.mark.unit


def _make_service(fake: FakeTTSBackend, **kwargs: object) -> AudioService:
    max_retries = int(kwargs.get("max_retries", 3))
    retry_backoff = float(kwargs.get("retry_backoff", 0.5))
    return AudioService(
        backend=fake,
        joiner=DirectMp3Joiner(),
        max_retries=max_retries,
        retry_backoff=retry_backoff,
    )


def test_format_rate() -> None:
    """Verifica a formatação de taxas percentuais para o edge-tts."""
    assert format_rate(0) == "+0%"
    assert format_rate(25) == "+25%"
    assert format_rate(-10) == "-10%"
    assert format_rate(100) == "+100%"
    assert format_rate(-50) == "-50%"


def test_list_voices_sucesso() -> None:
    """Listagem de vozes delega ao backend e filtra pelo locale pt-BR."""
    fake = FakeTTSBackend()
    service = _make_service(fake)

    voices = asyncio.run(service.list_voices("pt-BR"))
    assert len(voices) >= 1
    assert any(v.short_name == "pt-BR-AntonioNeural" for v in voices)


def test_synthesize_sucesso(tmp_path: Path) -> None:
    """Síntese completa de texto gera arquivo MP3 válido no caminho destino."""
    fake = FakeTTSBackend()
    service = _make_service(fake)

    dest = tmp_path / "saida.mp3"
    config = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=dest,
        rate_percent=0,
        collision_policy=CollisionPolicy.RENAME,
    )

    events: list[ProgressEvent] = []
    out_path, duration, size = asyncio.run(
        service.synthesize(
            text="Parágrafo de teste para narração de áudio.",
            config=config,
            progress=events.append,
        )
    )

    assert out_path == dest
    assert out_path.exists()
    assert size > 0
    assert duration > 0.0
    assert len(events) >= 3


def test_synthesize_texto_vazio_rejeitado(tmp_path: Path) -> None:
    """Texto em branco deve levantar SaidaInvalidaError imediatamente."""
    fake = FakeTTSBackend()
    service = _make_service(fake)
    config = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=tmp_path / "teste.mp3",
    )

    with pytest.raises(SaidaInvalidaError, match="vazio"):
        asyncio.run(service.synthesize(text="   ", config=config))


def test_synthesize_retentativa_transitoria(tmp_path: Path) -> None:
    """Falha de rede transitória (2 vezes) é retentada e tem sucesso na 3ª tentativa."""
    fake = FakeTTSBackend(fail_transient_attempts=2)
    service = _make_service(fake, max_retries=3, retry_backoff=0.01)

    dest = tmp_path / "retentativa.mp3"
    config = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=dest,
    )

    events: list[ProgressEvent] = []
    out_path, duration, _ = asyncio.run(
        service.synthesize(
            text="Texto que sofrerá instabilidade transitória.",
            config=config,
            progress=events.append,
        )
    )

    assert out_path.exists()
    assert duration > 0.0
    # Verifica que houve evento notificando a falha/retentativa
    assert any("Tentativa" in ev.message for ev in events)


def test_synthesize_falha_permanente_apos_limite(tmp_path: Path) -> None:
    """Se a falha de rede persistir além de max_retries, o erro é propagado."""
    fake = FakeTTSBackend(fail_transient_attempts=5)
    service = _make_service(fake, max_retries=2, retry_backoff=0.01)

    dest = tmp_path / "falha.mp3"
    config = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=dest,
    )

    with pytest.raises(TTSErroDeRedeError):
        asyncio.run(service.synthesize(text="Texto com falha permanente.", config=config))

    # Garante que nenhum arquivo final ou .part foi criado
    assert not dest.exists()
    assert not (tmp_path / "falha.mp3.part").exists()


def test_synthesize_cancelamento(tmp_path: Path) -> None:
    """Cancelamento interrompe o fluxo e não deixa arquivos parciais."""
    fake = FakeTTSBackend(latency_seconds=0.05)
    service = _make_service(fake)

    token = CancellationToken()
    dest = tmp_path / "cancelado.mp3"
    config = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=dest,
    )

    # Cancela logo antes de chamar
    token.cancel()

    with pytest.raises(CancelamentoError):
        asyncio.run(
            service.synthesize(
                text="Texto a ser cancelado.",
                config=config,
                cancel=token,
            )
        )

    assert not dest.exists()
    assert not (tmp_path / "cancelado.mp3.part").exists()


def test_synthesize_colisao_rename(tmp_path: Path) -> None:
    """Quando o arquivo já existe e a política é RENAME, salva com sufixo (1)."""
    fake = FakeTTSBackend()
    service = _make_service(fake)

    dest = tmp_path / "existente.mp3"
    dest.write_bytes(b"conteudo anterior")

    resolved_path = resolve_collision(dest, CollisionPolicy.RENAME)
    config = AudioJobConfig(
        voice="pt-BR-AntonioNeural",
        output_path=resolved_path,
        collision_policy=CollisionPolicy.RENAME,
    )

    out_path, _, _ = asyncio.run(
        service.synthesize(
            text="Novo áudio com colisão de nome.",
            config=config,
        )
    )

    assert out_path == tmp_path / "existente (1).mp3"
    assert out_path.exists()
    assert dest.read_bytes() == b"conteudo anterior"
