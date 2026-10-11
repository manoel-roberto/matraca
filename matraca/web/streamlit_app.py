"""Interface Web com Streamlit para o Matraca (RF-16, A.13.7).

Permite upload seguro de PDF, seleção de páginas e estratégias, prévia do texto
normalizado, síntese em segundo plano com barra de progresso, cancelamento
e download do MP3 gerado.
"""

from __future__ import annotations

import logging
import queue
import time
from pathlib import Path
from typing import Any

import streamlit as st

from matraca.core.exceptions import CancelamentoError, MatracaError
from matraca.core.job_service import JobService
from matraca.core.models import (
    AudioJobConfig,
    CollisionPolicy,
    JobResult,
    NarrationText,
    PDFInfo,
)
from matraca.core.page_selection import parse_page_selection
from matraca.core.progress import CancellationToken, ProgressEvent
from matraca.web.page_logic import (
    DEFAULT_MAX_UPLOAD_MB,
    UploadValidationError,
    WebSessionManager,
    build_web_job_service,
    estimate_duration_seconds,
    format_duration,
    format_file_size,
    validate_uploaded_pdf,
)

_log = logging.getLogger(__name__)


def _init_session_state() -> None:
    """Inicializa as variáveis de controle no session_state do Streamlit."""
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = WebSessionManager()
    if "pdf_path" not in st.session_state:
        st.session_state.pdf_path = None
    if "pdf_info" not in st.session_state:
        st.session_state.pdf_info = None
    if "preview" not in st.session_state:
        st.session_state.preview = None
    if "job_service" not in st.session_state:
        st.session_state.job_service = build_web_job_service()
    if "last_upload_name" not in st.session_state:
        st.session_state.last_upload_name = None


def render_privacy_warning() -> None:
    """Exibe alerta de privacidade e execução local (A.13.7, A.13.8)."""
    with st.expander("ℹ️ Informações Importantes & Privacidade", expanded=False):
        st.warning(
            "**Privacidade:** Esta aplicação foi projetada para execução local "
            "e não possui autenticação. Durante a síntese de áudio, o texto é "
            "transmitido via conexão segura aos servidores do serviço Microsoft Edge TTS. "
            "**Não envie documentos contendo informações sigilosas ou dados pessoais** "
            "caso não deseje transmiti-los.",
            icon="🛡️",
        )
        st.info(
            "**Dica de Concursos:** Para materiais do Estratégia Concursos, utilize a estratégia "
            "'Estratégia Concursos' para remover automaticamente cabeçalhos de aula, "
            "marcações de rodapé e números repetitivos de página.",
            icon="💡",
        )


def main() -> None:
    """Ponto de entrada da aplicação Streamlit."""
    st.set_page_config(
        page_title="Matraca",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session_state()
    sm: WebSessionManager = st.session_state.session_manager
    job_service: JobService = st.session_state.job_service

    st.title("🎧 Matraca — Leitor de PDFs para Concursos")
    st.caption("Transforme PDFs em áudio MP3 fluente em português do Brasil.")

    render_privacy_warning()

    # Barra lateral: Upload e configurações principais
    with st.sidebar:
        st.header("1. Documento PDF")
        uploaded_file = st.file_uploader(
            "Selecione o arquivo PDF",
            type=["pdf"],
            help=f"Tamanho máximo permitido: {DEFAULT_MAX_UPLOAD_MB} MB.",
        )

        if uploaded_file is not None:
            # Novo arquivo detectado
            if st.session_state.last_upload_name != uploaded_file.name:
                try:
                    data = uploaded_file.getvalue()
                    safe_name, valid_data = validate_uploaded_pdf(
                        uploaded_file.name,
                        data,
                        max_mb=DEFAULT_MAX_UPLOAD_MB,
                    )
                    saved_path = sm.save_upload(safe_name, valid_data)
                    info = job_service.inspect_pdf(saved_path)
                    st.session_state.pdf_path = saved_path
                    st.session_state.pdf_info = info
                    st.session_state.last_upload_name = uploaded_file.name
                    st.session_state.preview = None
                    st.success(f"PDF carregado: {safe_name} ({info.page_count} páginas)")
                except UploadValidationError as exc:
                    st.error(str(exc))
                    st.session_state.pdf_path = None
                    st.session_state.pdf_info = None
                    return
                except Exception as exc:
                    st.error(f"Falha ao processar PDF: {exc}")
                    st.session_state.pdf_path = None
                    st.session_state.pdf_info = None
                    return
        else:
            if st.session_state.pdf_path is not None:
                sm.cleanup()
                st.session_state.pdf_path = None
                st.session_state.pdf_info = None
                st.session_state.preview = None
                st.session_state.last_upload_name = None

        pdf_info: PDFInfo | None = st.session_state.pdf_info
        pdf_path: Path | None = st.session_state.pdf_path

        if pdf_info is not None and pdf_path is not None:
            st.divider()
            st.header("2. Seleção de Páginas")
            all_pages = st.checkbox("Todas as páginas", value=True)
            if all_pages:
                pages_expr = f"1-{pdf_info.page_count}"
                st.caption(f"Processando todas as {pdf_info.page_count} páginas.")
            else:
                pages_expr = st.text_input(
                    "Páginas ou intervalos",
                    value=f"1-{min(5, pdf_info.page_count)}",
                    help="Exemplos: 1-5, 8, 11-13",
                )

            st.divider()
            st.header("3. Extração & Voz")
            strategy_name = st.selectbox(
                "Estratégia de extração",
                options=["concursos", "default"],
                format_func=lambda s: (
                    "Estratégia Concursos (Recomendado)"
                    if s == "concursos"
                    else "Padrão (Genérico)"
                ),
            )

            voices = [
                ("pt-BR-FranciscaNeural", "Francisca (pt-BR, Feminina)"),
                ("pt-BR-AntonioNeural", "Antonio (pt-BR, Masculino)"),
                ("pt-BR-ThalitaNeural", "Thalita (pt-BR, Feminina)"),
            ]
            voice = st.selectbox(
                "Voz pt-BR",
                options=[v[0] for v in voices],
                index=0,
                format_func=lambda v: next(desc for code, desc in voices if code == v),
            )

            speed_pct = st.slider(
                "Velocidade da fala",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                format="%d%%",
                help="Ajuste fino da velocidade (-50% mais lento até +100% mais rápido).",
            )

            suggested_out = f"{pdf_path.stem}.mp3"
            output_name = st.text_input("Nome do arquivo MP3", value=suggested_out)

    # Painel principal
    if pdf_info is None or pdf_path is None:
        st.info("👈 Por favor, selecione um arquivo PDF na barra lateral para começar.")
        return

    # Validação prévia da seleção de páginas
    try:
        page_sel = parse_page_selection(pages_expr, pdf_info.page_count)
        valid_pages = True
    except Exception as exc:
        st.error(f"Seleção de páginas inválida: {exc}")
        valid_pages = False

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        preview_btn = st.button("🔍 Gerar Prévia do Texto", use_container_width=True)

    with col_btn2:
        generate_btn = st.button(
            "🚀 Iniciar Síntese de Áudio",
            type="primary",
            use_container_width=True,
            disabled=not valid_pages,
        )

    # Ação de prévia
    if preview_btn and valid_pages:
        with st.spinner("Extraindo e normalizando texto das páginas selecionadas..."):
            try:
                preview = job_service.get_preview(
                    pdf_path=pdf_path,
                    pages_expr=pages_expr,
                    strategy_name=strategy_name,
                )
                st.session_state.preview = preview
            except Exception as exc:
                st.error(f"Erro ao gerar prévia: {exc}")

    # Exibição da prévia
    current_preview: NarrationText | None = st.session_state.preview
    if current_preview is not None:
        st.subheader("Prévia do Conteúdo")
        tab_norm, tab_raw, tab_stats = st.tabs(
            ["📝 Texto Normalizado", "📄 Texto Bruto", "📊 Estatísticas"]
        )

        with tab_norm:
            st.text_area(
                "Texto que será narrado",
                value=current_preview.text,
                height=300,
                disabled=True,
            )

        with tab_raw:
            st.text_area(
                "Texto extraído do PDF",
                value=current_preview.original_text,
                height=300,
                disabled=True,
            )

        with tab_stats:
            char_count = len(current_preview.text)
            word_count = len(current_preview.text.split())
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Páginas Processadas", page_sel.count)
            col2.metric("Caracteres", char_count)
            col3.metric("Palavras", word_count)
            est_sec = estimate_duration_seconds(word_count, speed_pct)
            col4.metric("Duração Estimada", format_duration(est_sec))

            if current_preview.warnings:
                st.warning("Avisos durante a normalização:")
                for w in current_preview.warnings:
                    st.write(f"- {w}")

    # Ação de geração de áudio com acompanhamento e polling
    if generate_btn and valid_pages:
        st.subheader("Progresso da Síntese")
        prog_bar = st.progress(0.0)
        status_box = st.empty()
        cancel_box = st.empty()

        events: queue.Queue[ProgressEvent] = queue.Queue()
        cancel_token = CancellationToken()

        def _on_progress(event: ProgressEvent) -> None:
            events.put(event)

        job_result: dict[str, Any] = {"result": None, "error": None}

        def _on_complete(res: JobResult) -> None:
            job_result["result"] = res

        def _on_error(err: Exception) -> None:
            job_result["error"] = err

        out_path = sm.get_output_path(output_name)
        audio_config = AudioJobConfig(
            voice=voice,
            output_path=out_path,
            rate_percent=speed_pct,
            collision_policy=CollisionPolicy.OVERWRITE,
        )

        thread = job_service.run_job_in_thread(
            pdf_path=pdf_path,
            pages_expr=pages_expr,
            audio_config=audio_config,
            strategy_name=strategy_name,
            progress=_on_progress,
            cancel=cancel_token,
            on_complete=_on_complete,
            on_error=_on_error,
        )

        with cancel_box:
            if st.button("❌ Cancelar Síntese", key="btn_cancel_job"):
                cancel_token.cancel()
                status_box.warning("Cancelando processo...")

        # Loop de sincronização com a thread de trabalho
        while thread.is_alive() or not events.empty():
            while not events.empty():
                evt = events.get_nowait()
                prog_bar.progress(max(0.0, min(1.0, evt.fraction)))
                status_box.info(f"**{evt.stage.value.title()}:** {evt.message}")
            time.sleep(0.1)

        cancel_box.empty()

        if job_result["error"] is not None:
            err = job_result["error"]
            if isinstance(err, CancelamentoError):
                status_box.warning("Processamento cancelado pelo usuário.")
                prog_bar.progress(0.0)
            elif isinstance(err, MatracaError):
                status_box.error(f"Erro no processamento: {err}")
            else:
                status_box.error(f"Erro inesperado: {err}")
        elif job_result["result"] is not None:
            res: JobResult = job_result["result"]
            prog_bar.progress(1.0)
            status_box.success("🎉 Áudio MP3 gerado com sucesso!")

            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Tamanho do Arquivo", format_file_size(res.size_bytes))
            col_m2.metric(
                "Duração Estimada",
                format_duration(res.estimated_duration_seconds),
            )

            # Reprodução e download
            try:
                mp3_data = res.output_path.read_bytes()
                st.audio(mp3_data, format="audio/mp3")
                st.download_button(
                    label="📥 Baixar Arquivo MP3",
                    data=mp3_data,
                    file_name=res.output_path.name,
                    mime="audio/mpeg",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as read_exc:
                st.error(f"Não foi possível carregar o arquivo para download: {read_exc}")


if __name__ == "__main__":
    main()
