"""Escrita atômica e junção de arquivos MP3 com validação (RF-14, A.13.5)."""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import mutagen.mp3

from matraca.core.exceptions import SaidaInvalidaError

_log = logging.getLogger(__name__)


def validate_mp3_file(path: Path) -> float:
    """Valida se o arquivo MP3 existe, possui tamanho > 0 e duração válida.

    Retorna a duração em segundos.
    Lança SaidaInvalidaError se o arquivo estiver corrompido ou vazio.
    """
    if not path.exists():
        raise SaidaInvalidaError("Arquivo MP3 gerado não foi encontrado.")
    if path.stat().st_size == 0:
        raise SaidaInvalidaError("Arquivo MP3 gerado está vazio (tamanho 0 bytes).")

    try:
        audio = mutagen.mp3.MP3(str(path))  # type: ignore[no-untyped-call]
        info = audio.info
        if info is None or getattr(info, "length", 0.0) <= 0:
            raise SaidaInvalidaError("Arquivo MP3 possui duração inválida (zero ou negativa).")
        return float(info.length)
    except Exception as exc:
        raise SaidaInvalidaError(
            "Arquivo de áudio corrompido ou formato MP3 inválido.",
            detail=str(exc),
        ) from exc


class Mp3Joiner(Protocol):
    """Protocolo de junção de múltiplos arquivos MP3."""

    def join(self, segment_paths: Sequence[Path], dest_path: Path) -> float:
        """Concatena os segmentos em dest_path e retorna a duração total em segundos."""
        ...


class DirectMp3Joiner:
    """Juntador de MP3 por concatenação binária direta de streams homogêneos (ADR-014)."""

    def join(self, segment_paths: Sequence[Path], dest_path: Path) -> float:
        """Concatena múltiplos arquivos MP3 de forma atômica (.part -> os.replace).

        Retorna a duração total em segundos validada por mutagen.
        """
        if not segment_paths:
            raise SaidaInvalidaError("Nenhum segmento de áudio fornecido para junção.")

        dest_dir = dest_path.parent
        dest_dir.mkdir(parents=True, exist_ok=True)

        part_file = dest_path.with_name(f"{dest_path.name}.part")

        # Garante remoção de .part residual caso exista
        if part_file.exists():
            with contextlib_suppress():
                part_file.unlink()

        try:
            with open(part_file, "wb") as out_fp:
                for seg in segment_paths:
                    if not seg.exists() or seg.stat().st_size == 0:
                        raise SaidaInvalidaError(
                            "Segmento de áudio corrompido ou inexistente.",
                            detail=f"segment={seg}",
                        )
                    with open(seg, "rb") as in_fp:
                        shutil.copyfileobj(in_fp, out_fp, length=64 * 1024)

            # Valida integridade do arquivo antes de torná-lo oficial
            duration = validate_mp3_file(part_file)

            # Substituição atômica
            os.replace(part_file, dest_path)
            return duration

        except Exception as exc:
            # Limpeza estrita de qualquer .part em caso de erro
            if part_file.exists():
                with contextlib_suppress():
                    part_file.unlink()
            if isinstance(exc, SaidaInvalidaError):
                raise
            raise SaidaInvalidaError(
                "Falha ao gravar arquivo MP3 de saída.",
                detail=str(exc),
            ) from exc


class contextlib_suppress:
    """Supressor de exceções simples sem importar contextlib no loop."""

    def __enter__(self) -> None:
        pass

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> bool:
        return True
