"""Backend simulado de TTS para testes automatizados offline (A.12.6, RNF-02)."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path

from matraca.core.exceptions import (
    CancelamentoError,
    TTSErroDeRedeError,
    TTSErroDeServicoError,
    VozIndisponivelError,
)
from matraca.core.models import VoiceInfo
from matraca.core.progress import CancellationToken

# Caminho da fixture de MP3 sintético válido gerado para testes offline
_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "synthetic_sample.mp3"
)


class FakeTTSBackend:
    """TTSBackend simulado para testes sem acesso à rede externa."""

    def __init__(
        self,
        voices: Sequence[VoiceInfo] | None = None,
        *,
        fail_on_chunks: set[int] | None = None,
        fail_transient_attempts: int = 0,
        fail_permanently: bool = False,
        latency_seconds: float = 0.0,
    ) -> None:
        self.voices: list[VoiceInfo] = (
            list(voices)
            if voices is not None
            else [
                VoiceInfo(
                    short_name="pt-BR-AntonioNeural",
                    locale="pt-BR",
                    gender="Male",
                    friendly_name="Microsoft Antonio Online (Natural) - Portuguese (Brazil)",
                ),
                VoiceInfo(
                    short_name="pt-BR-FranciscaNeural",
                    locale="pt-BR",
                    gender="Female",
                    friendly_name="Microsoft Francisca Online (Natural) - Portuguese (Brazil)",
                ),
                VoiceInfo(
                    short_name="pt-BR-ThalitaMultilingualNeural",
                    locale="pt-BR",
                    gender="Female",
                    friendly_name="Microsoft ThalitaMultilingual Online pt-BR",
                ),
            ]
        )
        self.fail_on_chunks: set[int] = fail_on_chunks or set()
        self.fail_transient_attempts: int = fail_transient_attempts
        self.fail_permanently: bool = fail_permanently
        self.latency_seconds: float = latency_seconds

        self.calls: list[tuple[str, str, str, Path]] = []
        self._transient_attempt_counts: dict[str, int] = {}
        self.chunk_counter = 0

    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]:
        """Retorna as vozes configuradas."""
        if self.fail_permanently:
            raise TTSErroDeRedeError("Falha de rede simulada ao listar vozes.")
        res = [v for v in self.voices if locale.lower() in v.locale.lower()]
        if not res:
            raise VozIndisponivelError(f"Nenhuma voz para o locale {locale}.")
        return res

    async def synthesize_to_file(
        self,
        text: str,
        voice: str,
        rate: str,
        dest: Path,
        cancel: CancellationToken | None = None,
    ) -> None:
        """Simula a geração de um arquivo MP3 válido."""
        if cancel and cancel.is_cancelled:
            raise CancelamentoError("Síntese cancelada antes de iniciar.")

        idx = self.chunk_counter
        self.chunk_counter += 1
        self.calls.append((text, voice, rate, dest))

        if self.latency_seconds > 0:
            await asyncio.sleep(self.latency_seconds)

        if cancel and cancel.is_cancelled:
            raise CancelamentoError("Síntese cancelada durante execução.")

        if self.fail_permanently:
            raise TTSErroDeServicoError("Erro permanente de TTS simulado.")

        if idx in self.fail_on_chunks:
            raise TTSErroDeServicoError(f"Erro simulado no chunk {idx}.")

        if self.fail_transient_attempts > 0:
            dest_key = str(dest)
            count = self._transient_attempt_counts.get(dest_key, 0)
            if count < self.fail_transient_attempts:
                self._transient_attempt_counts[dest_key] = count + 1
                raise TTSErroDeRedeError(
                    f"Falha transitória na tentativa {count + 1} para {dest.name}."
                )

        dest.parent.mkdir(parents=True, exist_ok=True)

        if _FIXTURE_PATH.exists():
            dest.write_bytes(_FIXTURE_PATH.read_bytes())
        else:
            # Fallback seguro: grava bytes dummy caso fixture não esteja no caminho
            dest.write_bytes(b"\xff\xfb\x90\x64" + b"\x00" * 1024)
