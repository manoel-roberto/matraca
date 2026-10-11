"""Lógica da interface Web (Streamlit) do Matraca (RF-16, A.13.7).

Módulo desacoplado de Streamlit para facilitar testes unitários puros:
- Validação e sanitização de uploads de PDF;
- Verificação de cabeçalho mágico (%PDF-);
- Limite de tamanho configurável (maxUploadSize);
- Gerenciamento e isolamento de arquivos temporários por sessão;
- Formatação de taxas, tempos e estatísticas.
"""

from __future__ import annotations

import logging
import math
import shutil
import tempfile
import uuid
from pathlib import Path

from matraca.audio.edge_tts_client import EdgeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.config import MAX_UPLOAD_MB_DEFAULT
from matraca.core.audio_service import AudioService
from matraca.core.exceptions import MatracaError
from matraca.core.job_service import JobService
from matraca.core.pdf_service import PDFService
from matraca.core.ports import TTSBackend
from matraca.extractors.registry import default_registry
from matraca.pdf.pymupdf_reader import PyMuPDFReader
from matraca.utils.paths import sanitize_filename

_log = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_MB: int = MAX_UPLOAD_MB_DEFAULT
PDF_HEADER_MAGIC: bytes = b"%PDF-"


class UploadValidationError(MatracaError):
    """Erro de validação de arquivo de upload na interface Web."""


def validate_uploaded_pdf(
    raw_name: str,
    data: bytes,
    *,
    max_mb: int = DEFAULT_MAX_UPLOAD_MB,
) -> tuple[str, bytes]:
    """Valida tamanho, cabeçalho mágico e sanitiza o nome do PDF enviado.

    Raises:
        UploadValidationError: se o arquivo for vazio, exceder o tamanho limite
            ou não contiver o cabeçalho %PDF-.
    """
    if not data:
        raise UploadValidationError("O arquivo enviado está vazio (0 bytes).")

    max_bytes = max_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise UploadValidationError(
            f"O arquivo enviado possui {len(data) / (1024 * 1024):.1f} MB, "
            f"excedendo o limite máximo permitido de {max_mb} MB."
        )

    # Verifica se os primeiros 1024 bytes contêm o número mágico do PDF
    if PDF_HEADER_MAGIC not in data[:1024]:
        raise UploadValidationError(
            "O arquivo enviado não é um PDF válido: cabeçalho '%PDF-' não encontrado."
        )

    clean_name = sanitize_filename(raw_name, max_length=120, default="documento.pdf")
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"

    return clean_name, data


class WebSessionManager:
    """Gerencia o diretório temporário isolado por sessão web para uploads e saídas."""

    def __init__(self, session_id: str | None = None, base_dir: Path | None = None) -> None:
        self.session_id: str = session_id or uuid.uuid4().hex[:12]
        self._custom_base = base_dir
        self._dir: Path | None = None

    @property
    def dir(self) -> Path:
        """Cria e devolve o caminho do diretório temporário da sessão."""
        if self._dir is None or not self._dir.exists():
            if self._custom_base:
                self._dir = self._custom_base / f"matraca-web-{self.session_id}"
                self._dir.mkdir(parents=True, exist_ok=True)
            else:
                self._dir = Path(tempfile.mkdtemp(prefix=f"matraca-web-{self.session_id}-"))
        return self._dir

    def save_upload(self, filename: str, data: bytes) -> Path:
        """Grava os dados do PDF no diretório temporário da sessão com nome seguro."""
        safe_name = sanitize_filename(filename, max_length=120, default="documento.pdf")
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        target = self.dir / safe_name
        target.write_bytes(data)
        return target

    def get_output_path(self, suggested_name: str) -> Path:
        """Devolve um caminho seguro de saída MP3 dentro do diretório da sessão."""
        safe_stem = sanitize_filename(suggested_name, max_length=120, default="audio.mp3")
        if not safe_stem.lower().endswith(".mp3"):
            safe_stem += ".mp3"
        return self.dir / safe_stem

    def cleanup(self) -> None:
        """Remove o diretório temporário e todos os arquivos da sessão."""
        if self._dir is not None and self._dir.exists():
            shutil.rmtree(self._dir, ignore_errors=True)
            if self._dir.exists():
                _log.warning("Falha ao remover temporário web: %s", self._dir)
            self._dir = None


def format_rate_pct(rate_pct: int) -> str:
    """Formata a taxa de fala no padrão esperado pelo edge-tts (ex: '+0%', '+20%', '-15%')."""
    if rate_pct >= 0:
        return f"+{rate_pct}%"
    return f"{rate_pct}%"


def estimate_duration_seconds(word_count: int, rate_pct: int = 0) -> float:
    """Estima o tempo de fala em segundos baseado em 150 palavras/minuto e taxa de ajuste."""
    if word_count <= 0:
        return 0.0
    base_wpm = 150.0
    factor = max(0.2, 1.0 + (rate_pct / 100.0))
    effective_wpm = base_wpm * factor
    return (word_count / effective_wpm) * 60.0


def format_duration(seconds: float) -> str:
    """Formata segundos em uma string amigável em pt-BR (ex: '2 min 30 s' ou '45 s')."""
    if seconds <= 0:
        return "0 s"
    total_sec = math.ceil(seconds)
    mins = total_sec // 60
    secs = total_sec % 60
    if mins > 0:
        return f"{mins} min {secs} s"
    return f"{secs} s"


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em KB ou MB."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def build_web_job_service(tts_backend: TTSBackend | None = None) -> JobService:
    """Instancia o JobService com adaptadores de produção ou backend injetado."""
    pdf_service = PDFService(reader_factory=PyMuPDFReader)
    audio_service = AudioService(
        backend=tts_backend or EdgeTTSBackend(),
        joiner=DirectMp3Joiner(),
    )
    return JobService(
        pdf_service=pdf_service,
        audio_service=audio_service,
        registry=default_registry(),
    )
