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
from matraca.utils.logging_config import describe_text

_log = logging.getLogger(__name__)


def ensure_edge_tts_endpoint() -> None:
    """Garante compatibilidade com o endpoint atualizado da Microsoft (api.msedgeservices.com)."""
    try:
        from datetime import UTC
        from email.utils import parsedate_to_datetime

        import edge_tts.communicate as communicate
        import edge_tts.constants as constants
        import edge_tts.drm as drm

        # Redireciona endpoint de síntese se ainda apontar para speech.platform.bing.com
        if "speech.platform.bing.com" in getattr(constants, "WSS_URL", ""):
            new_wss = (
                "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
                f"?Ocp-Apim-Subscription-Key={constants.TRUSTED_CLIENT_TOKEN}"
            )
            constants.WSS_URL = new_wss
            communicate.WSS_URL = new_wss  # type: ignore[attr-defined]
            _log.info("Endpoint edge-tts configurado para api.msedgeservices.com")

        # Corrige parsing de data HTTP para funcionar em qualquer locale de sistema
        def _robust_parse_rfc2616_date(date: str) -> float | None:
            try:
                parsed = parsedate_to_datetime(date)
            except (TypeError, ValueError, IndexError):
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.timestamp()

        drm.DRM.parse_rfc2616_date = staticmethod(  # type: ignore[method-assign]
            _robust_parse_rfc2616_date
        )
    except Exception as exc:
        _log.warning("Não foi possível ajustar endpoint/DRM do edge-tts: %s", exc)


ensure_edge_tts_endpoint()


class EdgeTTSBackend:
    """Implementação real do TTSBackend baseada na biblioteca edge-tts 7.2.8."""

    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]:
        """Consulta as vozes disponíveis dinamicamente e filtra pelo locale."""
        ensure_edge_tts_endpoint()
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
        ensure_edge_tts_endpoint()
        _log.info(
            "Iniciando síntese TTS para %s com voz '%s' (taxa %s) -> %s",
            describe_text(text),
            voice,
            rate,
            dest.name,
        )

        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
            await communicate.save(str(dest))
            _log.info("Segmento sintetizado com sucesso: %s", dest.name)
        except Exception as exc:
            if cancel and cancel.is_cancelled:
                raise CancelamentoError("Síntese cancelada.") from exc

            _log.error("Erro ao sintetizar segmento %s: %s", dest.name, exc)
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
