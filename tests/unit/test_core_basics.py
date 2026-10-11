"""Testes de exceções, modelos, progresso e logging (RNF-03, RNF-04)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import pytest

from matraca.config import ExtractionConfig
from matraca.core.exceptions import (
    CancelamentoError,
    MatracaError,
    PDFInvalidoError,
    SelecaoPaginasError,
)
from matraca.core.models import AudioJobConfig, NarrationText, PageSelection
from matraca.core.progress import CancellationToken, ProgressEvent, Stage
from matraca.utils.logging_config import describe_text, setup_logging

pytestmark = pytest.mark.unit


def test_excecao_mensagem_amigavel_e_detalhe_separado() -> None:
    erro = PDFInvalidoError(detail="fitz: broken xref")
    assert "PDF" in erro.user_message
    assert str(erro) == erro.user_message
    assert "broken xref" not in str(erro)
    assert "broken xref" in erro.log_text()


def test_excecoes_herdam_de_matraca_error() -> None:
    assert issubclass(SelecaoPaginasError, MatracaError)
    assert issubclass(CancelamentoError, MatracaError)


def test_page_selection_all_e_validacoes() -> None:
    sel = PageSelection.all(3)
    assert sel.pages == (1, 2, 3)
    assert sel.count == 3
    with pytest.raises(ValueError):
        PageSelection("x", (), 3)
    with pytest.raises(ValueError):
        PageSelection("x", (2, 1), 3)
    with pytest.raises(ValueError):
        PageSelection("x", (1, 4), 3)


def test_narration_text_exige_alinhamento() -> None:
    with pytest.raises(ValueError):
        NarrationText(paragraphs=("a",), original_paragraphs=())
    texto = NarrationText(paragraphs=("a", "b"), original_paragraphs=("A", "B"))
    assert texto.text == "a\n\nb"
    assert texto.original_text == "A\n\nB"


def test_audio_job_config_valida_rate_e_voz(tmp_path: Path) -> None:
    AudioJobConfig(voice="pt-BR-X", output_path=tmp_path / "a.mp3", rate_percent=-50)
    with pytest.raises(ValueError):
        AudioJobConfig(voice="pt-BR-X", output_path=tmp_path / "a.mp3", rate_percent=101)
    with pytest.raises(ValueError):
        AudioJobConfig(voice=" ", output_path=tmp_path / "a.mp3")


def test_extraction_config_valida_limites() -> None:
    with pytest.raises(ValueError):
        ExtractionConfig(repeat_threshold=0.0)
    with pytest.raises(ValueError):
        ExtractionConfig(header_zone_pct=0.9)


def test_cancellation_token() -> None:
    token = CancellationToken()
    assert not token.is_cancelled
    token.raise_if_cancelled()
    threading.Timer(0.01, token.cancel).start()
    assert token.wait(2.0)
    with pytest.raises(CancelamentoError):
        token.raise_if_cancelled()


def test_progress_fraction() -> None:
    assert ProgressEvent(Stage.SYNTHESIZING, 1, 4).fraction == 0.25
    assert ProgressEvent(Stage.DONE).fraction == 0.0
    assert ProgressEvent(Stage.DONE, 9, 4).fraction == 1.0


def test_logging_nao_grava_conteudo_do_pdf(tmp_path: Path) -> None:
    segredo = "Texto sigiloso do concurso 123456"
    log_file = setup_logging(tmp_path, debug=True)
    logger = logging.getLogger("matraca.teste")
    logger.info("Extraído %s", describe_text(segredo))
    for handler in logging.getLogger("matraca").handlers:
        handler.flush()
    conteudo = log_file.read_text(encoding="utf-8")
    assert "len=" in conteudo
    assert segredo not in conteudo
    # limpeza dos handlers para não vazar entre testes
    for handler in list(logging.getLogger("matraca").handlers):
        logging.getLogger("matraca").removeHandler(handler)
        handler.close()


def test_setup_logging_idempotente(tmp_path: Path) -> None:
    setup_logging(tmp_path)
    setup_logging(tmp_path)
    marcados = [
        h for h in logging.getLogger("matraca").handlers if getattr(h, "_matraca_handler", False)
    ]
    assert len(marcados) == 1
    for handler in marcados:
        logging.getLogger("matraca").removeHandler(handler)
        handler.close()
