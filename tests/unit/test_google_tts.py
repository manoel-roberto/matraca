"""Testes unitários offline para GoogleCloudTTSBackend (RNF-02)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from matraca.audio.factory import TTSProvider, create_tts_backend
from matraca.audio.google_tts_client import GoogleCloudTTSBackend, parse_speaking_rate
from matraca.core.exceptions import (
    CancelamentoError,
    TTSErroDeRedeError,
    TTSErroDeServicoError,
    VozIndisponivelError,
)
from matraca.core.progress import CancellationToken


@pytest.mark.unit
def test_parse_speaking_rate() -> None:
    assert parse_speaking_rate("+0%") == 1.0
    assert parse_speaking_rate("0%") == 1.0
    assert parse_speaking_rate("+20%") == 1.2
    assert parse_speaking_rate("-10%") == 0.9
    assert parse_speaking_rate("+300%") == 4.0  # limit clamped at 4.0
    assert parse_speaking_rate("-90%") == 0.25  # limit clamped at 0.25
    assert parse_speaking_rate("invalido") == 1.0


@pytest.mark.unit
def test_create_tts_backend_factory() -> None:
    edge_b = create_tts_backend(TTSProvider.EDGE)
    assert edge_b.__class__.__name__ == "EdgeTTSBackend"

    google_b = create_tts_backend("google")
    assert isinstance(google_b, GoogleCloudTTSBackend)


@pytest.mark.unit
def test_google_list_voices_mocked() -> None:
    mock_client = MagicMock()

    # Cria vozes falsas do protobuf do Google
    v1 = MagicMock()
    v1.name = "pt-BR-Neural2-A"
    v1.language_codes = ["pt-BR"]
    v1.ssml_gender.name = "FEMALE"

    v2 = MagicMock()
    v2.name = "en-US-Standard-A"
    v2.language_codes = ["en-US"]
    v2.ssml_gender.name = "MALE"

    resp = MagicMock()
    resp.voices = [v1, v2]
    mock_client.list_voices.return_value = resp

    backend = GoogleCloudTTSBackend()
    backend._client = mock_client

    voices = asyncio.run(backend.list_voices("pt-BR"))
    assert len(voices) == 1
    assert voices[0].short_name == "pt-BR-Neural2-A"
    assert voices[0].gender == "Female"
    assert "Google pt-BR-Neural2-A" in str(voices[0].friendly_name)


@pytest.mark.unit
def test_google_list_voices_not_found() -> None:
    mock_client = MagicMock()
    resp = MagicMock()
    resp.voices = []
    mock_client.list_voices.return_value = resp

    backend = GoogleCloudTTSBackend()
    backend._client = mock_client

    with pytest.raises(VozIndisponivelError):
        asyncio.run(backend.list_voices("pt-BR"))


@pytest.mark.unit
def test_google_synthesize_to_file_mocked(tmp_path: Path) -> None:
    mock_client = MagicMock()
    fake_response = MagicMock()
    fake_response.audio_content = b"\xff\xfb\x90\x64" + b"\x00" * 256
    mock_client.synthesize_speech.return_value = fake_response

    backend = GoogleCloudTTSBackend()
    backend._client = mock_client

    dest = tmp_path / "segment.mp3"
    asyncio.run(backend.synthesize_to_file("Texto de teste.", "pt-BR-Neural2-A", "+10%", dest))

    assert dest.exists()
    assert dest.stat().st_size == len(fake_response.audio_content)
    mock_client.synthesize_speech.assert_called_once()


@pytest.mark.unit
def test_google_synthesize_cancellation(tmp_path: Path) -> None:
    backend = GoogleCloudTTSBackend()
    cancel = CancellationToken()
    cancel.cancel()

    dest = tmp_path / "cancel.mp3"
    with pytest.raises(CancelamentoError):
        asyncio.run(
            backend.synthesize_to_file("Texto.", "pt-BR-Neural2-A", "+0%", dest, cancel=cancel)
        )


@pytest.mark.unit
def test_google_synthesize_error_mapping(tmp_path: Path) -> None:
    mock_client = MagicMock()
    mock_client.synthesize_speech.side_effect = Exception("Connection timed out after 30000ms")

    backend = GoogleCloudTTSBackend()
    backend._client = mock_client

    dest = tmp_path / "err.mp3"
    with pytest.raises(TTSErroDeRedeError):
        asyncio.run(backend.synthesize_to_file("Texto.", "pt-BR-Neural2-A", "+0%", dest))

    mock_client.synthesize_speech.side_effect = Exception("PermissionDenied: 403 Forbidden")
    with pytest.raises(TTSErroDeServicoError):
        asyncio.run(backend.synthesize_to_file("Texto.", "pt-BR-Neural2-A", "+0%", dest))
