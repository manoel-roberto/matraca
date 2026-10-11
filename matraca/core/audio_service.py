"""Serviço de geração de áudio e orquestração do TTS (RF-11 a RF-14, RF-17, A.13.5)."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from matraca.audio.chunking import chunk_text
from matraca.core.exceptions import (
    CancelamentoError,
    SaidaInvalidaError,
    TTSErroDeRedeError,
)
from matraca.core.models import AudioJobConfig, VoiceInfo
from matraca.core.ports import Mp3Joiner, TTSBackend
from matraca.core.progress import CancellationToken, ProgressCallback, ProgressEvent, Stage

_log = logging.getLogger(__name__)


def format_rate(rate_percent: int) -> str:
    """Formata taxa percentual para o formato aceito pelo edge-tts (ex: '+20%', '-10%', '+0%')."""
    if rate_percent >= 0:
        return f"+{rate_percent}%"
    return f"{rate_percent}%"


class AudioService:
    """Orquestrador da síntese de fala e geração do arquivo de áudio."""

    def __init__(
        self,
        backend: TTSBackend,
        joiner: Mp3Joiner,
        *,
        chunk_max_chars: int = 1500,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ) -> None:
        self.backend = backend
        self.joiner = joiner
        self.chunk_max_chars = chunk_max_chars
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]:
        """Consulta as vozes disponíveis para o locale."""
        return await self.backend.list_voices(locale=locale)

    async def synthesize(
        self,
        text: str,
        config: AudioJobConfig,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> tuple[Path, float, int]:
        """Sintetiza texto em áudio e salva no arquivo final.

        Retorna (output_path, duration_seconds, size_bytes).
        """
        if not text.strip():
            raise SaidaInvalidaError("Texto para narração está vazio.")

        final_target = config.output_path

        # 1. Segmenta o texto
        chunks = chunk_text(text, max_chars=self.chunk_max_chars)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise SaidaInvalidaError("Nenhum segmento de texto pôde ser gerado para narração.")

        rate_str = format_rate(config.rate_percent)

        def emit(stage: Stage, current: int, total: int, msg: str) -> None:
            if progress:
                progress(ProgressEvent(stage=stage, current=current, total=total, message=msg))

        emit(
            Stage.SYNTHESIZING,
            0,
            total_chunks,
            f"Iniciando síntese de {total_chunks} segmento(s)...",
        )

        # 2. Sintetiza segmentos em pasta temporária isolada
        with tempfile.TemporaryDirectory(prefix="matraca_audio_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            segment_paths: list[Path] = []

            for i, chunk in enumerate(chunks, 1):
                if cancel and cancel.is_cancelled:
                    emit(Stage.CANCELLED, i - 1, total_chunks, "Síntese cancelada.")
                    raise CancelamentoError("Geração de áudio cancelada pelo usuário.")

                emit(
                    Stage.SYNTHESIZING,
                    i,
                    total_chunks,
                    f"Sintetizando segmento {i} de {total_chunks}...",
                )

                seg_dest = tmp_path / f"segment_{i:04d}.mp3"

                # Loop de retentativas para erros de rede transitórios
                attempt = 0
                while True:
                    if cancel and cancel.is_cancelled:
                        raise CancelamentoError("Geração de áudio cancelada.")
                    try:
                        await self.backend.synthesize_to_file(
                            text=chunk,
                            voice=config.voice,
                            rate=rate_str,
                            dest=seg_dest,
                            cancel=cancel,
                        )
                        break
                    except TTSErroDeRedeError:
                        attempt += 1
                        if attempt > self.max_retries:
                            emit(
                                Stage.ERROR,
                                i,
                                total_chunks,
                                f"Falha na rede após {self.max_retries} tentativas.",
                            )
                            raise
                        wait_sec = self.retry_backoff * (2 ** (attempt - 1))
                        msg_retry = (
                            f"Falha na rede no segmento {i}. "
                            f"Tentativa {attempt}/{self.max_retries} em {wait_sec:.1f}s..."
                        )
                        emit(Stage.SYNTHESIZING, i, total_chunks, msg_retry)
                        await asyncio.sleep(wait_sec)
                    except Exception as exc:
                        if cancel and cancel.is_cancelled:
                            raise CancelamentoError("Geração de áudio cancelada.") from exc
                        raise

                segment_paths.append(seg_dest)

            # 3. Junção atômica
            if cancel and cancel.is_cancelled:
                raise CancelamentoError("Cancelado antes da gravação final.")

            emit(Stage.FINALIZING, total_chunks, total_chunks, "Gravando arquivo final...")
            duration = self.joiner.join(segment_paths, final_target)
            size = final_target.stat().st_size

            emit(Stage.DONE, total_chunks, total_chunks, "Áudio gerado com sucesso!")
            return final_target, duration, size
