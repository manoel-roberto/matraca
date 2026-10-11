"""Testes unitários de escrita atômica e junção de MP3 (RF-14, A.13.5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from matraca.audio.mp3_writer import DirectMp3Joiner, validate_mp3_file
from matraca.core.exceptions import SaidaInvalidaError

pytestmark = pytest.mark.unit

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "synthetic_sample.mp3"


def test_join_mp3_sucesso(tmp_path: Path) -> None:
    """Dois segmentos de MP3 são concatenados atomicamente e validados com mutagen."""
    seg1 = tmp_path / "seg1.mp3"
    seg2 = tmp_path / "seg2.mp3"
    out_file = tmp_path / "final.mp3"

    sample_bytes = _FIXTURE_PATH.read_bytes()
    seg1.write_bytes(sample_bytes)
    seg2.write_bytes(sample_bytes)

    joiner = DirectMp3Joiner()
    duration = joiner.join([seg1, seg2], out_file)

    assert out_file.exists()
    assert out_file.stat().st_size == len(sample_bytes) * 2
    assert duration > 0.0

    # Garante que nenhum .part permaneceu
    part_file = tmp_path / "final.mp3.part"
    assert not part_file.exists()


def test_join_mp3_sem_segmentos_lanca_erro(tmp_path: Path) -> None:
    """Tentar unir lista vazia de segmentos deve lançar SaidaInvalidaError."""
    joiner = DirectMp3Joiner()
    with pytest.raises(SaidaInvalidaError, match="Nenhum segmento"):
        joiner.join([], tmp_path / "vazio.mp3")


def test_join_mp3_segmento_inexistente(tmp_path: Path) -> None:
    """Segmento que não existe deve interromper e limpar .part."""
    joiner = DirectMp3Joiner()
    inexistente = tmp_path / "nao_existe.mp3"
    dest = tmp_path / "saida.mp3"

    with pytest.raises(SaidaInvalidaError):
        joiner.join([inexistente], dest)

    assert not dest.exists()
    assert not (tmp_path / "saida.mp3.part").exists()


def test_join_mp3_segmento_vazio(tmp_path: Path) -> None:
    """Segmento com 0 bytes deve lançar SaidaInvalidaError."""
    vazio = tmp_path / "zero.mp3"
    vazio.write_bytes(b"")
    dest = tmp_path / "saida.mp3"

    joiner = DirectMp3Joiner()
    with pytest.raises(SaidaInvalidaError, match="corrompido ou inexistente"):
        joiner.join([vazio], dest)

    assert not dest.exists()
    assert not (tmp_path / "saida.mp3.part").exists()


def test_validate_mp3_arquivo_invalido(tmp_path: Path) -> None:
    """Arquivo de lixo binário não é aceito como MP3."""
    lixo = tmp_path / "lixo.mp3"
    lixo.write_bytes(b"Este nao e um arquivo MP3 de verdade")

    with pytest.raises(SaidaInvalidaError, match="corrompido ou formato MP3 inválido"):
        validate_mp3_file(lixo)
