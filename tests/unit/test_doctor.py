"""Testes unitários do módulo doctor (diagnóstico do sistema)."""

from __future__ import annotations

import pytest

from matraca.doctor import (
    check_ffmpeg,
    check_module,
    check_python,
    check_tkinter,
    run_doctor,
)

pytestmark = pytest.mark.unit


def test_doctor_check_python() -> None:
    """Verificação da versão do Python deve passar no ambiente de teste (>= 3.11)."""
    res = check_python()
    assert res.status is True
    assert "OK" in res.message


def test_doctor_check_module_instalado() -> None:
    """Módulos instalados retornam status True."""
    res = check_module("mutagen")
    assert res.status is True


def test_doctor_check_module_ausente() -> None:
    """Módulo inexistente retorna status False sem lançar exceção não tratada."""
    res = check_module("modulo_inexistente_123456")
    assert res.status is False
    assert "Ausente ou com falha" in res.message


def test_doctor_check_ffmpeg_e_tkinter() -> None:
    """Verificações de ferramentas auxiliares retornam NamedTuple CheckResult válido."""
    res_ffmpeg = check_ffmpeg()
    assert res_ffmpeg.name == "FFmpeg"

    res_tk = check_tkinter()
    assert res_tk.name == "Tkinter"


def test_doctor_run_doctor_sem_tts(capsys: pytest.CaptureFixture[str]) -> None:
    """run_doctor() sem flag TTS executa todas as verificações essenciais e retorna 0."""
    code = run_doctor(check_tts=False)
    captured = capsys.readouterr()

    assert code == 0
    assert "Matraca — Diagnóstico do Sistema" in captured.out
    assert "AMBIENTE PRONTO PARA EXECUÇÃO" in captured.out
