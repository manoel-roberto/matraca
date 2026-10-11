"""Testes dos utilitários de caminho (RNF-04)."""

from __future__ import annotations

from pathlib import Path

import pytest

from matraca.core.exceptions import ArquivoJaExisteError, SaidaInvalidaError
from matraca.core.models import CollisionPolicy
from matraca.utils.paths import (
    job_tempdir,
    resolve_collision,
    sanitize_filename,
    validate_output_path,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("aula.pdf", "aula.pdf"),
        ("../../x.pdf", "x.pdf"),
        ("..\\..\\windows\\system32\\x.pdf", "x.pdf"),
        ("/etc/passwd", "passwd"),
        ("a:b*c?.pdf", "a_b_c_.pdf"),
        ("CON.pdf", "_CON.pdf"),
        ("nul", "_nul"),
        ("   ", "arquivo"),
        ("..", "arquivo"),
        ("", "arquivo"),
        ("nome\x00com\x1fcontrole.pdf", "nomecomcontrole.pdf"),
        ("arquivo.pdf.", "arquivo.pdf"),
        (".pdf", "pdf"),  # ponto inicial removido: evita arquivos ocultos
        ("acentuação ç.pdf", "acentuação ç.pdf"),
    ],
)
def test_sanitize_filename(entrada: str, esperado: str) -> None:
    assert sanitize_filename(entrada) == esperado


def test_sanitize_filename_limita_comprimento_preservando_extensao() -> None:
    resultado = sanitize_filename("a" * 500 + ".pdf", max_length=50)
    assert len(resultado) <= 50
    assert resultado.endswith(".pdf")


def test_sanitize_nunca_contem_separadores() -> None:
    for nome in ["a/b", "a\\b", "../..", "x/../y.pdf"]:
        resultado = sanitize_filename(nome)
        assert "/" not in resultado
        assert "\\" not in resultado
        assert ".." not in resultado


def test_colisao_rename(tmp_path: Path) -> None:
    alvo = tmp_path / "saida.mp3"
    alvo.write_bytes(b"x")
    (tmp_path / "saida (1).mp3").write_bytes(b"x")
    assert resolve_collision(alvo, CollisionPolicy.RENAME) == tmp_path / "saida (2).mp3"


def test_colisao_ask_levanta(tmp_path: Path) -> None:
    alvo = tmp_path / "saida.mp3"
    alvo.write_bytes(b"x")
    with pytest.raises(ArquivoJaExisteError):
        resolve_collision(alvo, CollisionPolicy.ASK)


def test_colisao_overwrite_e_sem_colisao(tmp_path: Path) -> None:
    alvo = tmp_path / "saida.mp3"
    assert resolve_collision(alvo, CollisionPolicy.ASK) == alvo
    alvo.write_bytes(b"x")
    assert resolve_collision(alvo, CollisionPolicy.OVERWRITE) == alvo


def test_validate_output_ok(tmp_path: Path) -> None:
    assert validate_output_path(tmp_path / "a.mp3") == (tmp_path / "a.mp3").resolve()


@pytest.mark.parametrize("nome", ["a.txt", "a"])
def test_validate_output_extensao(tmp_path: Path, nome: str) -> None:
    with pytest.raises(SaidaInvalidaError):
        validate_output_path(tmp_path / nome)


def test_validate_output_pasta_inexistente(tmp_path: Path) -> None:
    with pytest.raises(SaidaInvalidaError):
        validate_output_path(tmp_path / "nao_existe" / "a.mp3")


def test_validate_output_nao_sobrescreve_pdf_de_origem(tmp_path: Path) -> None:
    pdf = tmp_path / "a.mp3"
    pdf.write_bytes(b"x")
    with pytest.raises(SaidaInvalidaError):
        validate_output_path(pdf, source_pdf=pdf)


def test_job_tempdir_remove_ao_final_mesmo_com_erro() -> None:
    caminho: Path | None = None
    with pytest.raises(RuntimeError), job_tempdir() as tmp:
        caminho = tmp
        (tmp / "x.bin").write_bytes(b"1")
        raise RuntimeError("falha simulada")
    assert caminho is not None
    assert not caminho.exists()
