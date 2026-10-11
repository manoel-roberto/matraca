"""Diagnóstico do ambiente e verificação de saúde do sistema (RF-18, A.13.9)."""

from __future__ import annotations

import asyncio
import importlib
import platform
import shutil
import sys
import time
from typing import NamedTuple


class CheckResult(NamedTuple):
    name: str
    status: bool
    message: str
    critical: bool = True


def check_python() -> CheckResult:
    """Verifica versão mínima do Python (>= 3.11)."""
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 11):
        return CheckResult("Python >= 3.11", True, f"OK ({ver_str})")
    return CheckResult(
        "Python >= 3.11", False, f"Incompatível: {ver_str} (exige >= 3.11)", critical=True
    )


def check_module(mod_name: str, critical: bool = True) -> CheckResult:
    """Verifica importação e versão de módulos instalados."""
    try:
        mod = importlib.import_module(mod_name)
        ver = getattr(mod, "__version__", "instalado")
        return CheckResult(f"Módulo {mod_name}", True, f"OK ({ver})", critical=critical)
    except Exception as exc:
        return CheckResult(
            f"Módulo {mod_name}", False, f"Ausente ou com falha: {exc}", critical=critical
        )


def check_ffmpeg() -> CheckResult:
    """Verifica se o binário ffmpeg está no PATH do sistema."""
    path = shutil.which("ffmpeg")
    if path:
        return CheckResult("FFmpeg", True, f"OK ({path})", critical=False)
    return CheckResult(
        "FFmpeg",
        False,
        "Ausente (opcional para codecs adicionais; Matraca usa MP3 puro)",
        critical=False,
    )


def check_tkinter() -> CheckResult:
    """Verifica se a biblioteca Tkinter está disponível."""
    try:
        import tkinter

        return CheckResult("Tkinter", True, f"OK (Tcl/Tk {tkinter.TkVersion})", critical=False)
    except Exception as exc:
        return CheckResult(
            "Tkinter",
            False,
            f"Indisponível ({exc}). Necessário python3-tk para a interface Desktop.",
            critical=False,
        )


async def check_tts_service() -> CheckResult:
    """Testa conectividade e tempo de resposta real do edge-tts."""
    try:
        edge_tts_mod = importlib.import_module("edge_tts")

        t0 = time.perf_counter()
        voices = await edge_tts_mod.list_voices()
        elapsed = (time.perf_counter() - t0) * 1000
        pt_voices = [v for v in voices if "pt-BR" in v.get("Locale", "")]
        return CheckResult(
            "Conectividade TTS (edge-tts)",
            True,
            f"OK ({len(pt_voices)} vozes pt-BR encontradas em {elapsed:.0f} ms)",
            critical=False,
        )
    except Exception as exc:
        return CheckResult(
            "Conectividade TTS (edge-tts)",
            False,
            f"Falha de conexão ({exc}). Verifique sua internet ou firewall.",
            critical=False,
        )


def run_doctor(*, check_tts: bool = False) -> int:
    """Executa todas as verificações do ambiente e imprime relatório formatado."""
    print("=" * 60)
    print(" Matraca — Diagnóstico do Sistema (doctor)")
    print("=" * 60)
    print(f"Sistema Operacional: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Executável Python:  {sys.executable}")
    print("-" * 60)

    results: list[CheckResult] = [
        check_python(),
        check_module("fitz"),
        check_module("edge_tts"),
        check_module("customtkinter", critical=False),
        check_module("streamlit", critical=False),
        check_module("mutagen"),
        check_ffmpeg(),
        check_tkinter(),
    ]

    if check_tts:
        print("Testando serviço de síntese TTS remoto...")
        tts_result = asyncio.run(check_tts_service())
        results.append(tts_result)

    has_critical_failure = False

    for r in results:
        status_tag = "✓" if r.status else ("✗" if r.critical else "!")
        print(f" [{status_tag}] {r.name: <30}: {r.message}")
        if not r.status and r.critical:
            has_critical_failure = True

    print("=" * 60)
    if has_critical_failure:
        print("STATUS: FALHA CRÍTICA — Instale as dependências faltantes.")
        return 1

    print("STATUS: AMBIENTE PRONTO PARA EXECUÇÃO.")
    return 0
