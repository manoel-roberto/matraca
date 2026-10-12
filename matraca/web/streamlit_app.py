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

from matraca.audio.edge_tts_client import EdgeTTSBackend
from matraca.audio.google_tts_client import GoogleCloudTTSBackend
from matraca.core.custom_strategy import CustomStrategyConfig
from matraca.core.exceptions import CancelamentoError, EstrategiaInvalidaError, MatracaError
from matraca.core.job_service import JobService
from matraca.core.models import (
    AudioJobConfig,
    CollisionPolicy,
    JobResult,
    NarrationText,
    PDFInfo,
)
from matraca.core.page_selection import parse_page_selection
from matraca.core.ports import TTSBackend
from matraca.core.progress import CancellationToken, ProgressEvent
from matraca.pdf.pymupdf_reader import PyMuPDFReader
from matraca.utils.credentials import (
    find_google_credentials,
    save_google_credentials,
    validate_service_account_file,
)
from matraca.utils.logging_config import setup_logging
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


@st.cache_data(show_spinner=False)
def get_page_thumbnail_cached(
    pdf_path_str: str,
    page_number: int,
    max_dimension: int = 250,
) -> bytes:
    """Renderiza a miniatura de uma página do PDF com cache estrito do Streamlit."""
    reader = PyMuPDFReader(Path(pdf_path_str))
    with reader:
        return reader.render_page_thumbnail(page_number, max_dimension=max_dimension)


def render_pages_thumbnail_viewer(
    pdf_path: Path,
    pages: list[int],
    max_thumbnails: int = 20,
) -> None:
    """Exibe o expander com grid de miniaturas para confirmação visual das páginas."""
    with st.expander("Páginas Selecionadas (Visualização)", expanded=True):
        if not pages:
            st.info("Nenhuma página selecionada para visualização.")
            return

        to_show = pages[:max_thumbnails]
        total = len(pages)
        st.caption(
            f"Confirmação visual: exibindo **{len(to_show)}** de "
            f"**{total}** página(s) selecionada(s)."
        )

        cols = st.columns(4)
        for idx, page_num in enumerate(to_show):
            col = cols[idx % 4]
            with col:
                try:
                    thumb_bytes = get_page_thumbnail_cached(str(pdf_path), page_num)
                    st.image(
                        thumb_bytes,
                        caption=f"Página {page_num}",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"Pág. {page_num}: {exc}")

        if total > max_thumbnails:
            st.info(
                f"➕ **+ {total - max_thumbnails} página(s)** selecionada(s) "
                f"além das {max_thumbnails} exibidas acima."
            )


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


def render_strategy_manager(job_service: JobService) -> None:
    """Aba do Gerenciador de Estratégias Customizadas (CRUD)."""
    st.subheader("⚙️ Gerenciador de Estratégias Customizadas")
    st.caption(
        "Crie, visualize, edite e remova estratégias de normalização e remoção de ruídos "
        "para seus materiais de estudo sem alterar o código-fonte."
    )

    custom_strategies = job_service.list_custom_strategies()
    options = ["+ Criar Nova Estratégia"] + [s.name for s in custom_strategies]

    def _format_choice(opt: str) -> str:
        if opt == "+ Criar Nova Estratégia":
            return "➕ Criar Nova Estratégia"
        strat_obj = next((s for s in custom_strategies if s.name == opt), None)
        return f"{strat_obj.display_name} ({opt})" if strat_obj else opt

    selected_option = st.selectbox(
        "Selecione uma estratégia para editar:",
        options=options,
        format_func=_format_choice,
        key="selected_strat_mgr",
    )

    is_new = selected_option == "+ Criar Nova Estratégia"
    current_strat = (
        next((s for s in custom_strategies if s.name == selected_option), None)
        if not is_new
        else None
    )

    with st.form(key=f"form_strategy_{selected_option}"):
        col_id, col_disp = st.columns(2)
        with col_id:
            strat_name = st.text_input(
                "ID Interno (nome único):",
                value="" if is_new or current_strat is None else current_strat.name,
                disabled=not is_new,
                help="Apenas letras, números e sublinhados (ex: meu_curso_x).",
            )
        with col_disp:
            display_name = st.text_input(
                "Nome de Exibição:",
                value="" if is_new or current_strat is None else current_strat.display_name,
                help="Nome amigável exibido nos seletores (ex: Meu Curso X).",
            )

        patterns_default = (
            "\n".join(current_strat.noise_patterns)
            if current_strat and current_strat.noise_patterns
            else ""
        )
        noise_text = st.text_area(
            "Padrões de Ruído (Regex — uma por linha):",
            value=patterns_default,
            height=120,
            help="Expressões regulares para remover cabeçalhos, rodapés ou marcas d'água.",
        )

        st.markdown("**Dicionário de Siglas e Pronúncias:**")
        st.caption(
            "Adicione siglas e suas pronúncias expandidas para leitura correta pelo sintetizador."
        )

        initial_acronyms: list[dict[str, str]] = []
        if current_strat and current_strat.acronyms:
            for k, v in current_strat.acronyms.items():
                initial_acronyms.append({"Sigla": k, "Pronúncia": v})

        edited_data = st.data_editor(
            initial_acronyms,
            num_rows="dynamic",
            column_config={
                "Sigla": st.column_config.TextColumn("Sigla (ex: PGE)", required=True),
                "Pronúncia": st.column_config.TextColumn(
                    "Pronúncia (ex: Procuradoria Geral do Estado)", required=True
                ),
            },
            use_container_width=True,
            key=f"data_editor_acronyms_{selected_option}",
        )

        col_save, col_del = st.columns([3, 1])
        with col_save:
            btn_save = st.form_submit_button(
                "💾 Salvar Estratégia",
                type="primary",
                use_container_width=True,
            )
        with col_del:
            btn_del = st.form_submit_button(
                "🗑️ Excluir Estratégia",
                disabled=is_new,
                use_container_width=True,
            )

    if btn_save:
        target_name = (strat_name or "").strip()
        target_display = (display_name or "").strip() or target_name
        noise_lines = [line.strip() for line in noise_text.strip().splitlines() if line.strip()]

        acronyms_dict: dict[str, str] = {}
        if isinstance(edited_data, list):
            for row in edited_data:
                if isinstance(row, dict):
                    s = str(row.get("Sigla", "") or "").strip()
                    p = str(row.get("Pronúncia", "") or "").strip()
                    if s and p:
                        acronyms_dict[s] = p
        elif hasattr(edited_data, "iterrows"):
            for _, row in edited_data.iterrows():
                s = str(row.get("Sigla", "") or "").strip()
                p = str(row.get("Pronúncia", "") or "").strip()
                if s and p:
                    acronyms_dict[s] = p

        if not target_name:
            st.error("Informe o ID interno da estratégia.")
            return

        try:
            cfg = CustomStrategyConfig(
                name=target_name,
                display_name=target_display,
                noise_patterns=tuple(noise_lines),
                acronyms=acronyms_dict,
            )
            job_service.save_custom_strategy(cfg)
            st.toast(f"Estratégia '{target_display}' salva com sucesso!", icon="✅")
            st.success(f"Estratégia '{target_display}' salva com sucesso!")
            time.sleep(0.5)
            st.rerun()
        except (EstrategiaInvalidaError, Exception) as exc:
            st.error(f"Erro ao salvar estratégia: {exc}")

    if btn_del and not is_new and current_strat:
        try:
            job_service.delete_custom_strategy(current_strat.name)
            st.toast(f"Estratégia '{current_strat.name}' excluída!", icon="🗑️")
            st.success(f"Estratégia '{current_strat.name}' excluída com sucesso!")
            time.sleep(0.5)
            st.rerun()
        except Exception as exc:
            st.error(f"Erro ao excluir estratégia: {exc}")


def _render_conversor(
    job_service: JobService,
    sm: WebSessionManager,
    pdf_info: PDFInfo,
    pdf_path: Path,
    pages_expr: str,
    strategy_name: str,
    voice: str,
    speed_pct: int,
    output_name: str,
) -> None:
    """Renderiza os controles e resultados da conversão de PDF para áudio."""
    try:
        page_sel = parse_page_selection(pages_expr, pdf_info.page_count)
        valid_pages = True
    except Exception as exc:
        st.error(f"Seleção de páginas inválida: {exc}")
        valid_pages = False

    if valid_pages:
        render_pages_thumbnail_viewer(pdf_path, list(page_sel.pages), max_thumbnails=20)

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


def main() -> None:
    """Ponto de entrada da aplicação Streamlit."""
    setup_logging()
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
                except Exception as exc:
                    st.error(f"Falha ao processar PDF: {exc}")
                    st.session_state.pdf_path = None
                    st.session_state.pdf_info = None
        else:
            if st.session_state.pdf_path is not None:
                sm.cleanup()
                st.session_state.pdf_path = None
                st.session_state.pdf_info = None
                st.session_state.preview = None
                st.session_state.last_upload_name = None

        pdf_info: PDFInfo | None = st.session_state.pdf_info
        pdf_path: Path | None = st.session_state.pdf_path

        pages_expr = ""
        strategy_name = "concursos"
        voice = "pt-BR-FranciscaNeural"
        speed_pct = 0
        output_name = "audio.mp3"

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
            available_strategies = job_service.get_selectable_strategies()
            strat_map = dict(available_strategies)
            strat_options = [k for k, _ in available_strategies]
            def_idx = strat_options.index("concursos") if "concursos" in strat_options else 0
            strategy_name = st.selectbox(
                "Estratégia de extração",
                options=strat_options,
                index=def_idx,
                format_func=lambda s: strat_map.get(s, s),
            )

            st.markdown("**Provedor de Voz (TTS)**")
            tts_provider = st.radio(
                "Serviço TTS",
                options=["edge", "google"],
                format_func=lambda p: (
                    "Microsoft Edge TTS (Gratuito)"
                    if p == "edge"
                    else "Google Cloud Text-to-Speech (API)"
                ),
                label_visibility="collapsed",
                key="web_tts_provider_choice",
            )

            tts_backend: TTSBackend
            if tts_provider == "google":
                cred_path = find_google_credentials()
                if cred_path:
                    try:
                        summary = validate_service_account_file(cred_path)
                        st.caption(
                            f"✅ Credenciais ativas: `{cred_path.name}` "
                            f"(Projeto: **{summary['project_id']}**)"
                        )
                    except Exception as exc:
                        st.warning(f"Credencial com erro: {exc}")

                uploaded_cred = st.file_uploader(
                    "Importar arquivo credenciais.json",
                    type=["json"],
                    help="Envie a chave JSON de conta de serviço Google Cloud.",
                    key="uploader_credenciais_json",
                )
                if uploaded_cred is not None:
                    try:
                        saved_path, summary = save_google_credentials(uploaded_cred.getvalue())
                        st.success(
                            f"✅ Credenciais conectadas: {saved_path.name} "
                            f"(Projeto: {summary['project_id']})"
                        )
                        cred_path = saved_path
                    except Exception as exc:
                        st.error(f"Arquivo inválido: {exc}")

                tts_backend = GoogleCloudTTSBackend(cred_path)
                voices = [
                    ("pt-BR-Neural2-A", "Google Neural2-A (Feminina, Alta Fidelidade)"),
                    ("pt-BR-Neural2-B", "Google Neural2-B (Masculino, Alta Fidelidade)"),
                    ("pt-BR-Neural2-C", "Google Neural2-C (Feminina, Alta Fidelidade)"),
                    ("pt-BR-Wavenet-A", "Google Wavenet-A (Feminina)"),
                    ("pt-BR-Wavenet-B", "Google Wavenet-B (Masculino)"),
                    ("pt-BR-Chirp3-HD-Achernar", "Google Chirp3-HD Achernar (Feminina, HD)"),
                    ("pt-BR-Chirp3-HD-Achird", "Google Chirp3-HD Achird (Masculino, HD)"),
                ]
            else:
                tts_backend = EdgeTTSBackend()
                voices = [
                    ("pt-BR-FranciscaNeural", "Francisca (pt-BR, Feminina)"),
                    ("pt-BR-AntonioNeural", "Antonio (pt-BR, Masculino)"),
                    ("pt-BR-ThalitaMultilingualNeural", "Thalita (pt-BR, Feminina)"),
                ]

            job_service.audio_service.backend = tts_backend

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

    # Painel principal organizado em abas
    tab_conversor, tab_estrategias = st.tabs(
        ["🎧 Conversor de PDF", "⚙️ Gerenciador de Estratégias"]
    )

    with tab_estrategias:
        render_strategy_manager(job_service)

    with tab_conversor:
        if pdf_info is None or pdf_path is None:
            st.info("👈 Por favor, selecione um arquivo PDF na barra lateral para começar.")
        else:
            _render_conversor(
                job_service=job_service,
                sm=sm,
                pdf_info=pdf_info,
                pdf_path=pdf_path,
                pages_expr=pages_expr,
                strategy_name=strategy_name,
                voice=voice,
                speed_pct=speed_pct,
                output_name=output_name,
            )


if __name__ == "__main__":
    main()
