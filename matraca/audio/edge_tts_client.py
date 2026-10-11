"""Adaptador para o serviço edge-tts (RF-11, A.12.6, ADR-013)."""

from __future__ import annotations

import logging
from pathlib import Path

import edge_tts

from matraca.core.exceptions import (
    CancelamentoError,
    TTSErroDeRedeError,
    TTSErroDeServicoError,
    VozIndisponivelError,
)
from matraca.core.models import VoiceInfo
from matraca.core.progress import CancellationToken

_log = logging.getLogger(__name__)


class EdgeTTSBackend:
    """Implementação real do TTSBackend baseada na biblioteca edge-tts 7.2.8."""

    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]:
        """Consulta as vozes disponíveis dinamicamente e filtra pelo locale."""
        try:
            raw_voices = await edge_tts.list_voices()
        except Exception as exc:
            raise TTSErroDeRedeError(
                "Não foi possível consultar as vozes disponíveis. Verifique sua conexão.",
                detail=str(exc),
            ) from exc

        voices: list[VoiceInfo] = []
        for v in raw_voices:
            v_locale = v.get("Locale", "")
            if locale.lower() in v_locale.lower():
                voices.append(
                    VoiceInfo(
                        short_name=v.get("ShortName", ""),
                        locale=v_locale,
                        gender=v.get("Gender"),
                        friendly_name=v.get("FriendlyName"),
                    )
                )

        if not voices:
            raise VozIndisponivelError(
                f"Nenhuma voz encontrada para o idioma {locale}.",
                detail=f"locale={locale}",
            )

        return voices

    async def synthesize_to_file(
        self,
        text: str,
        voice: str,
        rate: str,
        dest: Path,
        cancel: CancellationToken | None = None,
    ) -> None:
        """Sintetiza o texto em áudio MP3 e salva no caminho de destino."""
        if cancel and cancel.is_cancelled:
            raise CancelamentoError("Síntese de áudio cancelada antes do início.")

        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
            await communicate.save(str(dest))
        except Exception as exc:
            if cancel and cancel.is_cancelled:
                raise CancelamentoError("Síntese cancelada.") from exc

            err_str = str(exc).lower()
            if (
                "timeout" in err_str
                or "connection" in err_str
                or "network" in err_str
                or "nodename" in err_str
            ):
                raise TTSErroDeRedeError(
                    "Falha de conexão com o serviço de voz. Verifique sua internet.",
                    detail=str(exc),
                ) from exc
            raise TTSErroDeServicoError(
                "O serviço de voz retornou um erro ao processar o segmento.",
                detail=str(exc),
            ) from exc

        if cancel and cancel.is_cancelled:
            if dest.exists():
                dest.unlink(missing_ok=True)
            raise CancelamentoError("Síntese de áudio cancelada.")
