"""Testes unitários e de integração para a lógica da interface Web (RF-16, A.13.7)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from matraca.audio.fake_tts import FakeTTSBackend
from matraca.core.models import AudioJobConfig, CollisionPolicy
from matraca.web.page_logic import (
    UploadValidationError,
    WebSessionManager,
    build_web_job_service,
    estimate_duration_seconds,
    format_duration,
    format_file_size,
    format_rate_pct,
    validate_uploaded_pdf,
)

pytestmark = pytest.mark.unit

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_validate_uploaded_pdf_success() -> None:
    data = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n"
    name, valid_data = validate_uploaded_pdf("meu_documento.pdf", data)
    assert name == "meu_documento.pdf"
    assert valid_data == data


def test_validate_uploaded_pdf_sanitization() -> None:
    data = b"%PDF-1.4\nraw pdf content"
    malicious_names = [
        ("../../ataque.pdf", "ataque.pdf"),
        ("..\\..\\windows\\system32\\calc.pdf", "calc.pdf"),
        ("documento sem extensao", "documento sem extensao.pdf"),
        ("CON.pdf", "_CON.pdf"),
        ("arquivo com <caracteres:proibidos>*.pdf", "arquivo com _caracteres_proibidos__.pdf"),
    ]
    for raw, expected in malicious_names:
        clean_name, _ = validate_uploaded_pdf(raw, data)
        assert clean_name == expected
        assert not clean_name.startswith(("../", "..\\"))
        assert clean_name.endswith(".pdf")


def test_validate_uploaded_pdf_empty_error() -> None:
    with pytest.raises(UploadValidationError, match="vazio"):
        validate_uploaded_pdf("vazio.pdf", b"")


def test_validate_uploaded_pdf_size_limit_error() -> None:
    data = b"%PDF-1.4" + b"x" * (2 * 1024 * 1024)
    with pytest.raises(UploadValidationError, match="excedendo o limite máximo"):
        validate_uploaded_pdf("pesado.pdf", data, max_mb=1)


def test_validate_uploaded_pdf_invalid_header_error() -> None:
    fake_binary = b"\x7fELF\x02\x01\x01\x00NotAPdfAtAll"
    with pytest.raises(UploadValidationError, match="cabeçalho '%PDF-' não encontrado"):
        validate_uploaded_pdf("binario.pdf", fake_binary)

    fake_text = b"Ola mundo, este e apenas um arquivo txt"
    with pytest.raises(UploadValidationError, match="cabeçalho '%PDF-' não encontrado"):
        validate_uploaded_pdf("texto.pdf", fake_text)


def test_web_session_manager_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        base = Path(tmp_root)
        manager = WebSessionManager(session_id="test1234", base_dir=base)

        session_dir = manager.dir
        assert session_dir.exists()
        assert session_dir.is_dir()
        assert "matraca-web-test1234" in session_dir.name

        pdf_data = b"%PDF-1.7\nteste"
        saved = manager.save_upload("../../arquivo.pdf", pdf_data)
        assert saved.exists()
        assert saved.name == "arquivo.pdf"
        assert saved.read_bytes() == pdf_data

        out_path = manager.get_output_path("minha_aula")
        assert out_path.name == "minha_aula.mp3"
        assert out_path.parent == session_dir

        manager.cleanup()
        assert not session_dir.exists()


def test_format_helpers() -> None:
    assert format_rate_pct(0) == "+0%"
    assert format_rate_pct(25) == "+25%"
    assert format_rate_pct(-15) == "-15%"

    assert estimate_duration_seconds(0) == 0.0
    # 150 palavras em velocidade 0% = 1 minuto (60 s)
    assert round(estimate_duration_seconds(150, 0), 1) == 60.0
    # 150 palavras em velocidade +50% (+50% WPM -> 225 WPM) = 40 s
    assert round(estimate_duration_seconds(150, 50), 1) == 40.0

    assert format_duration(0) == "0 s"
    assert format_duration(45) == "45 s"
    assert format_duration(125) == "2 min 5 s"

    assert format_file_size(500 * 1024) == "500.0 KB"
    assert format_file_size(2 * 1024 * 1024) == "2.00 MB"


def test_web_job_service_preview_and_run(tmp_path: Path) -> None:
    import asyncio

    fixture_pdf = _FIXTURES_DIR / "sinteticos" / "uma_coluna.pdf"
    if not fixture_pdf.exists():
        pytest.skip("Fixture sintética uma_coluna.pdf não encontrada.")

    fake_tts = FakeTTSBackend()
    job_service = build_web_job_service(fake_tts)

    # 1. Prévia do texto
    preview = job_service.get_preview(
        pdf_path=fixture_pdf,
        pages_expr="1",
        strategy_name="concursos",
    )
    assert len(preview.text) > 0
    assert len(preview.paragraphs) > 0

    # 2. Execução de síntese
    out_file = tmp_path / "web_teste.mp3"
    audio_cfg = AudioJobConfig(
        voice="pt-BR-FranciscaNeural",
        output_path=out_file,
        rate_percent=10,
        collision_policy=CollisionPolicy.OVERWRITE,
    )

    result = asyncio.run(
        job_service.run_job_async(
            pdf_path=fixture_pdf,
            pages_expr="1",
            audio_config=audio_cfg,
            strategy_name="concursos",
        )
    )

    assert result.output_path == out_file
    assert result.output_path.exists()
    assert result.size_bytes > 0


def test_streamlit_app_test_initialization() -> None:
    """Verifica que o app Streamlit inicializa sem erros na árvore de componentes."""
    try:
        from streamlit.testing.v1 import AppTest
    except ImportError:
        pytest.skip("streamlit.testing.v1.AppTest não disponível.")

    root_app = Path(__file__).resolve().parents[2] / "app_web.py"
    at = AppTest.from_file(str(root_app))
    at.run()

    # O app deve renderizar a tela inicial limpa sem lançar exceções não tratadas
    assert not at.exception
    # Deve conter o título principal e o file uploader
    assert any("Matraca" in str(title.value) for title in at.title)


def test_get_page_thumbnail_cached() -> None:
    from matraca.web.streamlit_app import get_page_thumbnail_cached

    fixture_pdf = _FIXTURES_DIR / "uma_coluna.pdf"
    thumb1 = get_page_thumbnail_cached(str(fixture_pdf), 1, max_dimension=200)
    assert isinstance(thumb1, bytes)
    assert thumb1.startswith(b"\x89PNG\r\n\x1a\n")

    # Segunda chamada recupera do cache estrito do Streamlit sem erro
    thumb2 = get_page_thumbnail_cached(str(fixture_pdf), 1, max_dimension=200)
    assert thumb1 == thumb2
