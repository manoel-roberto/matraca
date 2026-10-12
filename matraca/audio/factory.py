"""Fábrica de backends de TTS para alternar entre provedores (Edge TTS e Google Cloud)."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from matraca.audio.edge_tts_client import EdgeTTSBackend
from matraca.audio.google_tts_client import GoogleCloudTTSBackend
from matraca.core.ports import TTSBackend


class TTSProvider(StrEnum):
    """Provedores de síntese de fala suportados pelo Matraca."""

    EDGE = "edge"
    GOOGLE = "google"


def create_tts_backend(
    provider: TTSProvider | str = TTSProvider.EDGE,
    *,
    google_credentials_path: Path | str | None = None,
    google_credentials_info: dict[str, Any] | None = None,
) -> TTSBackend:
    """Instancia o backend de síntese correspondente ao provedor informado."""
    prov_str = str(provider).lower()
    if prov_str in (TTSProvider.GOOGLE, "google", "gcp"):
        return GoogleCloudTTSBackend(
            credentials_path=google_credentials_path,
            credentials_info=google_credentials_info,
        )
    return EdgeTTSBackend()
