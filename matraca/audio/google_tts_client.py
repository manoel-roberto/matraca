"""Adaptador para o serviço Google Cloud Text-to-Speech API (RF-11, A.12.6).

Permite síntese de voz alternativa de alta fidelidade autenticada via chave de conta
de serviço (credenciais.json), sem expor chaves no código ou versionamento.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from matraca.core.exceptions import (
    CancelamentoError,
    TTSErroDeRedeError,
    TTSErroDeServicoError,
    VozIndisponivelError,
)
from matraca.core.models import VoiceInfo
from matraca.core.progress import CancellationToken
from matraca.utils.credentials import find_google_credentials, validate_service_account_file
from matraca.utils.logging_config import describe_text

_log = logging.getLogger(__name__)


def parse_speaking_rate(rate: str) -> float:
    """Converte o formato de taxa do Matraca ('+20%', '-10%', '+0%') para speaking_rate do Google.

    O Google Cloud TTS espera um float entre 0.25 e 4.0, onde 1.0 é a velocidade normal.
    """
    try:
        clean = rate.replace("%", "").strip()
        pct = float(clean)
        speed = 1.0 + (pct / 100.0)
        return max(0.25, min(4.0, round(speed, 2)))
    except (ValueError, TypeError):
        return 1.0


class GoogleCloudTTSBackend:
    """Implementação de TTSBackend baseada no Google Cloud Text-to-Speech."""

    def __init__(
        self,
        credentials_path: Path | str | None = None,
        credentials_info: dict[str, Any] | None = None,
    ) -> None:
        self.credentials_path = find_google_credentials(credentials_path)
        self.credentials_info = credentials_info
        self._client: Any = None

    def is_configured(self) -> bool:
        """Verifica se existem credenciais válidas configuradas."""
        if self.credentials_info:
            return True
        return self.credentials_path is not None and self.credentials_path.is_file()

    def get_credentials_summary(self) -> dict[str, str] | None:
        """Retorna resumo público da conta de serviço conectada (project_id, client_email)."""
        if self.credentials_info:
            from matraca.utils.credentials import validate_service_account_dict

            return validate_service_account_dict(self.credentials_info)
        if self.credentials_path:
            try:
                return validate_service_account_file(self.credentials_path)
            except Exception:
                return None
        return None

    def _get_client(self) -> Any:
        """Inicializa e retorna o cliente oficial do Google Cloud Text-to-Speech."""
        if self._client is not None:
            return self._client

        try:
            from google.cloud import texttospeech
        except ImportError as exc:
            raise TTSErroDeServicoError(
                "A biblioteca 'google-cloud-texttospeech' não está instalada. "
                "Execute: pip install google-cloud-texttospeech",
                detail=str(exc),
            ) from exc

        try:
            if self.credentials_info:
                self._client = texttospeech.TextToSpeechClient.from_service_account_info(
                    self.credentials_info
                )
            elif self.credentials_path:
                self._client = texttospeech.TextToSpeechClient.from_service_account_json(
                    str(self.credentials_path)
                )
            else:
                # Tenta credenciais padrão do ambiente se disponíveis
                resolved = find_google_credentials()
                if resolved:
                    self.credentials_path = resolved
                    self._client = texttospeech.TextToSpeechClient.from_service_account_json(
                        str(resolved)
                    )
                else:
                    raise TTSErroDeServicoError(
                        "Credenciais do Google Cloud Text-to-Speech não encontradas. "
                        "Importe o arquivo 'credenciais.json' nas configurações de voz.",
                        detail="credentials_not_found",
                    )
        except Exception as exc:
            if isinstance(exc, TTSErroDeServicoError):
                raise
            raise TTSErroDeServicoError(
                f"Falha ao carregar credenciais do Google Cloud: {exc}",
                detail=str(exc),
            ) from exc

        return self._client

    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]:
        """Consulta as vozes disponíveis na API do Google Cloud e filtra pelo locale."""
        client = self._get_client()

        def _fetch_voices() -> Any:
            return client.list_voices(language_code=locale)

        try:
            response = await asyncio.to_thread(_fetch_voices)
        except Exception as exc:
            err_str = str(exc).lower()
            if "timeout" in err_str or "connection" in err_str or "unavailable" in err_str:
                raise TTSErroDeRedeError(
                    "Falha de conexão com a API Google Cloud TTS ao listar vozes.",
                    detail=str(exc),
                ) from exc
            raise TTSErroDeServicoError(
                f"Erro na API Google Cloud TTS ao listar vozes: {exc}",
                detail=str(exc),
            ) from exc

        voices: list[VoiceInfo] = []
        for v in response.voices:
            # Verifica se o locale bate com um dos códigos de idioma da voz
            matches_locale = any(locale.lower() in code.lower() for code in v.language_codes)
            if not matches_locale:
                continue

            gender_name = getattr(v.ssml_gender, "name", "NEUTRAL").upper()
            if gender_name == "FEMALE":
                gender = "Female"
            elif gender_name == "MALE":
                gender = "Male"
            else:
                gender = "Neutral"

            # Nome amigável legível (ex: Google pt-BR-Neural2-A (Female))
            friendly = f"Google {v.name} ({gender})"
            voices.append(
                VoiceInfo(
                    short_name=v.name,
                    locale=locale,
                    gender=gender,
                    friendly_name=friendly,
                )
            )

        if not voices:
            raise VozIndisponivelError(
                f"Nenhuma voz do Google Cloud encontrada para o idioma {locale}.",
                detail=f"locale={locale}",
            )

        # Ordenação intuitiva: Neural2 e Wavenet primeiro, seguidas por Chirp3 e Standard
        def _sort_priority(v: VoiceInfo) -> tuple[int, str]:
            name = v.short_name
            if "Neural2" in name:
                return (0, name)
            if "Wavenet" in name:
                return (1, name)
            if "Chirp" in name:
                return (2, name)
            if "Studio" in name:
                return (3, name)
            if "Standard" in name:
                return (4, name)
            return (5, name)

        voices.sort(key=_sort_priority)
        return voices

    async def synthesize_to_file(
        self,
        text: str,
        voice: str,
        rate: str,
        dest: Path,
        cancel: CancellationToken | None = None,
    ) -> None:
        """Sintetiza texto em MP3 usando a API do Google Cloud Text-to-Speech."""
        if cancel and cancel.is_cancelled:
            raise CancelamentoError("Síntese de áudio cancelada antes do início.")

        dest.parent.mkdir(parents=True, exist_ok=True)
        client = self._get_client()
        speaking_rate = parse_speaking_rate(rate)

        _log.info(
            "Iniciando síntese Google TTS para %s com voz '%s' (velocidade %.2f) -> %s",
            describe_text(text),
            voice,
            speaking_rate,
            dest.name,
        )

        def _do_synthesize() -> bytes:
            from google.cloud import texttospeech

            locale_prefix = "-".join(voice.split("-")[:2]) if "-" in voice else "pt-BR"
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=locale_prefix,
                name=voice,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
            )
            resp = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )
            return bytes(resp.audio_content)

        try:
            audio_bytes = await asyncio.to_thread(_do_synthesize)
        except Exception as exc:
            if cancel and cancel.is_cancelled:
                raise CancelamentoError("Síntese cancelada.") from exc

            _log.error("Erro ao sintetizar segmento com Google TTS %s: %s", dest.name, exc)
            err_str = str(exc).lower()
            if (
                "timeout" in err_str
                or "connection" in err_str
                or "unavailable" in err_str
                or "deadline" in err_str
            ):
                raise TTSErroDeRedeError(
                    "Falha de conexão com a API Google Cloud TTS. Verifique sua internet.",
                    detail=str(exc),
                ) from exc
            if "permission" in err_str or "unauthenticated" in err_str or "403" in err_str:
                raise TTSErroDeServicoError(
                    "Erro de autenticação ou permissão na API Google Cloud TTS. "
                    "Verifique se o arquivo credenciais.json é válido e se a "
                    "Cloud Text-to-Speech API está ativada no projeto.",
                    detail=str(exc),
                ) from exc
            if "resource_exhausted" in err_str or "quota" in err_str or "429" in err_str:
                raise TTSErroDeServicoError(
                    "Cota ou limite de requisições do Google Cloud excedido.",
                    detail=str(exc),
                ) from exc
            raise TTSErroDeServicoError(
                f"A API Google Cloud TTS retornou um erro ao processar o segmento: {exc}",
                detail=str(exc),
            ) from exc

        if cancel and cancel.is_cancelled:
            if dest.exists():
                dest.unlink(missing_ok=True)
            raise CancelamentoError("Síntese de áudio cancelada.")

        dest.write_bytes(audio_bytes)
        _log.info(
            "Segmento sintetizado com sucesso via Google TTS (%d bytes): %s",
            len(audio_bytes),
            dest.name,
        )
