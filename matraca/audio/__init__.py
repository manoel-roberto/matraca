"""Pacote de áudio e síntese de voz do Matraca."""

from matraca.audio.edge_tts_client import EdgeTTSBackend
from matraca.audio.factory import TTSProvider, create_tts_backend
from matraca.audio.google_tts_client import GoogleCloudTTSBackend

__all__ = [
    "EdgeTTSBackend",
    "GoogleCloudTTSBackend",
    "TTSProvider",
    "create_tts_backend",
]
