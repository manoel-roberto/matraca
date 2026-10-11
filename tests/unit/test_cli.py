"""Testes unitários da interface de linha de comando CLI (RF-18, A.13.9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from matraca.cli import main

pytestmark = pytest.mark.unit


def test_cli_sem_argumentos_imprime_ajuda(capsys: pytest.CaptureFixture[str]) -> None:
    """Execução sem parâmetros exibe a mensagem de ajuda e sai com código 0."""
    code = main([])
    captured = capsys.readouterr()
    assert code == 0
    assert "usage: python -m matraca" in captured.out


def test_cli_doctor(capsys: pytest.CaptureFixture[str]) -> None:
    """Subcomando doctor executa o diagnóstico do sistema e sai com código 0."""
    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Matraca — Diagnóstico do Sistema" in captured.out


def test_cli_run_arquivo_inexistente(capsys: pytest.CaptureFixture[str]) -> None:
    """Subcomando run com PDF inexistente informa erro na stderr e retorna 1."""
    code = main(["run", "inexistente_123456.pdf"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Arquivo PDF não encontrado" in captured.err


def test_cli_run_preview(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Subcomando run com --preview chama get_preview e exibe estatísticas."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"
    pdf_path = fixtures_dir / "uma_coluna.pdf"

    code = main(["run", str(pdf_path), "--pages", "1", "--preview"])
    captured = capsys.readouterr()

    assert code == 0
    assert "Gerando prévia" in captured.out
    assert "Estatísticas" in captured.out
