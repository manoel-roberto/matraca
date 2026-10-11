"""Interface de linha de comando mínima do Matraca (RF-18, A.13.9)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from matraca.audio.edge_tts_client import EdgeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.core.audio_service import AudioService
from matraca.core.exceptions import MatracaError
from matraca.core.job_service import JobService
from matraca.core.models import AudioJobConfig, CollisionPolicy
from matraca.core.pdf_service import PDFService
from matraca.doctor import run_doctor
from matraca.extractors.registry import default_registry
from matraca.pdf.pymupdf_reader import PyMuPDFReader


def _build_default_job_service() -> JobService:
    """Instancia o JobService com adaptadores de produção."""
    pdf_service = PDFService(reader_factory=PyMuPDFReader)
    audio_service = AudioService(backend=EdgeTTSBackend(), joiner=DirectMp3Joiner())
    return JobService(
        pdf_service=pdf_service,
        audio_service=audio_service,
        registry=default_registry(),
    )


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI do Matraca."""
    parser = argparse.ArgumentParser(
        prog="python -m matraca",
        description="Matraca — Transforma PDFs em áudio MP3 para estudo de concursos públicos.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ser executado")

    # Subcomando doctor
    doc_parser = subparsers.add_parser("doctor", help="Diagnóstico do ambiente e dependências")
    doc_parser.add_argument(
        "--tts",
        action="store_true",
        help="Testa conectividade real com o serviço remoto de TTS",
    )

    # Subcomando run
    run_parser = subparsers.add_parser("run", help="Processa um PDF para MP3 ou gera prévia")
    run_parser.add_argument("pdf", type=Path, help="Caminho do arquivo PDF de entrada")
    run_parser.add_argument(
        "--pages",
        default="",
        help="Seleção de páginas (ex: 1, 3, 5-10). Padrão: todas as páginas.",
    )
    run_parser.add_argument(
        "--mode",
        default="concursos",
        help="Estratégia de extração (concursos, default). Padrão: concursos.",
    )
    run_parser.add_argument(
        "--voice",
        default="pt-BR-AntonioNeural",
        help="Voz pt-BR do TTS. Padrão: pt-BR-AntonioNeural.",
    )
    run_parser.add_argument(
        "--rate",
        type=int,
        default=0,
        help="Ajuste de velocidade percentual (-50 a +100). Padrão: 0.",
    )
    run_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Caminho do arquivo MP3 de saída. Padrão: mesmo nome do PDF com extensão .mp3.",
    )
    run_parser.add_argument(
        "--preview",
        action="store_true",
        help="Apenas exibe prévia do texto e estatísticas sem sintetizar áudio.",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "doctor":
        return run_doctor(check_tts=args.tts)

    if args.command == "run":
        pdf_path: Path = args.pdf
        if not pdf_path.exists():
            print(f"Erro: Arquivo PDF não encontrado: {pdf_path}", file=sys.stderr)
            return 1

        service = _build_default_job_service()

        try:
            info = service.inspect_pdf(pdf_path)
            pages_expr = args.pages.strip() if args.pages else f"1-{info.page_count}"

            if args.preview:
                print(f"Gerando prévia para {pdf_path.name} (páginas: {pages_expr})...")
                preview = service.get_preview(
                    pdf_path=pdf_path,
                    pages_expr=pages_expr,
                    strategy_name=args.mode,
                )
                print("\n--- Estatísticas ---")
                for k, v in preview.stats.items():
                    print(f"  {k}: {v}")
                print("\n--- Amostra do Texto Normalizado (primeiros 3 parágrafos) ---")
                sample = "\n\n".join(preview.paragraphs[:3])
                print(sample or "(nenhum texto)")
                return 0

            out_path: Path = args.out or pdf_path.with_suffix(".mp3")
            audio_config = AudioJobConfig(
                voice=args.voice,
                output_path=out_path,
                rate_percent=args.rate,
                collision_policy=CollisionPolicy.RENAME,
            )

            print(f"Iniciando conversão de {pdf_path.name} para {out_path.name}...")

            def _progress(ev: object) -> None:
                msg = getattr(ev, "message", "")
                if msg:
                    print(f" -> {msg}")

            result = asyncio.run(
                service.run_job_async(
                    pdf_path=pdf_path,
                    pages_expr=pages_expr,
                    audio_config=audio_config,
                    strategy_name=args.mode,
                    progress=_progress,
                )
            )

            print("\nConcluído com sucesso!")
            print(f"Arquivo gerado: {result.output_path}")
            print(f"Tamanho:        {result.size_bytes / 1024:.1f} KB")
            print(f"Duração aprox.: {result.estimated_duration_seconds:.1f} segundos")
            return 0

        except MatracaError as exc:
            print(f"Erro no Matraca: {exc.user_message}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Erro inesperado: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
