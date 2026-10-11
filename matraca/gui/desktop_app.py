"""Interface gráfica Desktop do Matraca com CustomTkinter (RF-15, A.13.6)."""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from matraca.audio.edge_tts_client import EdgeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.core.audio_service import AudioService
from matraca.core.job_service import JobService
from matraca.core.models import JobResult, NarrationText, PDFInfo, VoiceInfo
from matraca.core.pdf_service import PDFService
from matraca.extractors.registry import default_registry
from matraca.gui.presenter import DesktopPresenter, UIState
from matraca.pdf.pymupdf_reader import PyMuPDFReader

_log = logging.getLogger(__name__)


class DesktopApp(ctk.CTk):
    """Janela principal da aplicação Desktop do Matraca."""

    def __init__(self, presenter: DesktopPresenter | None = None) -> None:
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Matraca - Leitor de PDFs")
        self.geometry("900x700")
        self.minsize(800, 600)

        self.presenter = presenter or self._build_default_presenter()
        self._voices_cache: list[VoiceInfo] = []

        self._init_ui()
        self.presenter.init_voices()

        # Inicia o polling de eventos da fila da thread trabalhadora
        self._on_tick()

    def _build_default_presenter(self) -> DesktopPresenter:
        pdf_service = PDFService(reader_factory=PyMuPDFReader)
        audio_service = AudioService(backend=EdgeTTSBackend(), joiner=DirectMp3Joiner())
        job_service = JobService(
            pdf_service=pdf_service,
            audio_service=audio_service,
            registry=default_registry(),
        )
        return DesktopPresenter(view=self, job_service=job_service)

    def _init_ui(self) -> None:
        # Layout principal com padding e expansão
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        container.grid_columnconfigure(1, weight=1)

        row = 0

        # 1. Seleção de PDF
        ctk.CTkLabel(container, text="Arquivo PDF:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=6
        )
        self.pdf_entry = ctk.CTkEntry(container, placeholder_text="Selecione um PDF...")
        self.pdf_entry.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        self.btn_browse = ctk.CTkButton(
            container, text="Procurar...", width=100, command=self._on_browse_pdf
        )
        self.btn_browse.grid(row=row, column=2, sticky="e", pady=6)

        row += 1
        self.lbl_pdf_info = ctk.CTkLabel(
            container, text="Nenhum arquivo carregado.", text_color="gray"
        )
        self.lbl_pdf_info.grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        # 2. Páginas
        ctk.CTkLabel(container, text="Páginas:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=6
        )
        pages_frame = ctk.CTkFrame(container, fg_color="transparent")
        pages_frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        pages_frame.grid_columnconfigure(0, weight=1)

        self.pages_entry = ctk.CTkEntry(pages_frame, placeholder_text="Ex: 1, 3, 5-10")
        self.pages_entry.grid(row=0, column=0, sticky="ew", padx=(8, 16))

        self.chk_all_pages_var = ctk.BooleanVar(value=True)
        self.chk_all_pages = ctk.CTkCheckBox(
            pages_frame,
            text="Todas as páginas",
            variable=self.chk_all_pages_var,
            command=self._on_all_pages_toggle,
        )
        self.chk_all_pages.grid(row=0, column=1, sticky="e")

        row += 1
        # 3. Estratégia de Extração
        ctk.CTkLabel(container, text="Estratégia:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=6
        )
        self.combo_strategy = ctk.CTkComboBox(
            container,
            values=["concursos (Estratégia Concursos)", "default (Padrão)"],
        )
        self.combo_strategy.grid(row=row, column=1, sticky="w", padx=8, pady=6)

        row += 1
        # 4. Voz e Velocidade
        ctk.CTkLabel(container, text="Voz pt-BR:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=6
        )
        self.combo_voice = ctk.CTkComboBox(container, values=["pt-BR-AntonioNeural"], width=300)
        self.combo_voice.grid(row=row, column=1, sticky="w", padx=8, pady=6)

        row += 1
        ctk.CTkLabel(container, text="Velocidade (%):", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=6
        )
        rate_frame = ctk.CTkFrame(container, fg_color="transparent")
        rate_frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        rate_frame.grid_columnconfigure(0, weight=1)

        self.slider_rate = ctk.CTkSlider(
            rate_frame,
            from_=-50,
            to=100,
            number_of_steps=30,
            command=self._on_rate_slider,
        )
        self.slider_rate.set(0)
        self.slider_rate.grid(row=0, column=0, sticky="ew", padx=8)

        self.lbl_rate_val = ctk.CTkLabel(rate_frame, text="0%", width=60)
        self.lbl_rate_val.grid(row=0, column=1, sticky="e")

        row += 1
        # 5. Caminho de Saída
        ctk.CTkLabel(container, text="Salvar MP3 em:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=6
        )
        self.out_entry = ctk.CTkEntry(container, placeholder_text="Destino do áudio .mp3...")
        self.out_entry.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        self.btn_browse_out = ctk.CTkButton(
            container, text="Salvar como...", width=100, command=self._on_browse_out
        )
        self.btn_browse_out.grid(row=row, column=2, sticky="e", pady=6)

        row += 1
        # 6. Ações (Prévia, Iniciar, Cancelar)
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=16)
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_preview = ctk.CTkButton(
            actions_frame,
            text="Ver Prévia do Texto",
            command=self._on_preview_click,
            fg_color="gray50",
        )
        self.btn_preview.grid(row=0, column=0, padx=6, sticky="ew")

        self.btn_start = ctk.CTkButton(
            actions_frame,
            text="Iniciar Conversão",
            command=self._on_start_click,
            fg_color="green",
        )
        self.btn_start.grid(row=0, column=1, padx=6, sticky="ew")

        self.btn_cancel = ctk.CTkButton(
            actions_frame,
            text="Cancelar",
            command=self._on_cancel_click,
            fg_color="red",
            state="disabled",
        )
        self.btn_cancel.grid(row=0, column=2, padx=6, sticky="ew")

        row += 1
        # 7. Progresso e Estado
        self.progress_bar = ctk.CTkProgressBar(container)
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)

        row += 1
        self.lbl_status = ctk.CTkLabel(container, text="Pronto.", font=ctk.CTkFont(weight="bold"))
        self.lbl_status.grid(row=row, column=0, columnspan=3, sticky="w", pady=4)

    # --- Métodos de evento da UI ---

    def _on_tick(self) -> None:
        """Consome a fila do worker a cada 50ms."""
        self.presenter.poll_events()
        self.after(50, self._on_tick)

    def _on_browse_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o arquivo PDF",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if path:
            p = Path(path)
            self.pdf_entry.delete(0, "end")
            self.pdf_entry.insert(0, str(p))
            self.presenter.on_pdf_selected(p)

    def _on_browse_out(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Salvar áudio MP3",
            defaultextension=".mp3",
            filetypes=[("Áudio MP3", "*.mp3")],
        )
        if path:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, path)

    def _on_all_pages_toggle(self) -> None:
        if self.chk_all_pages_var.get():
            self.pages_entry.configure(state="disabled")
            if self.presenter.pdf_info:
                self.pages_entry.delete(0, "end")
                self.pages_entry.insert(0, f"1-{self.presenter.pdf_info.page_count}")
        else:
            self.pages_entry.configure(state="normal")

    def _on_rate_slider(self, val: float) -> None:
        self.lbl_rate_val.configure(text=f"{int(val)}%")

    def _get_pages_expr(self) -> str:
        if self.chk_all_pages_var.get() and self.presenter.pdf_info:
            return f"1-{self.presenter.pdf_info.page_count}"
        return str(self.pages_entry.get()).strip()

    def _get_strategy_name(self) -> str:
        val = str(self.combo_strategy.get())
        if "default" in val:
            return "default"
        return "concursos"

    def _on_preview_click(self) -> None:
        pages_expr = self._get_pages_expr()
        strat = self._get_strategy_name()
        self.presenter.on_preview_requested(pages_expr=pages_expr, strategy_name=strat)

    def _on_start_click(self) -> None:
        pages_expr = self._get_pages_expr()
        voice = self.combo_voice.get().split()[0]
        rate = int(self.slider_rate.get())
        out_str = self.out_entry.get().strip()
        strat = self._get_strategy_name()

        if not out_str:
            messagebox.showwarning("Aviso", "Selecione o caminho de destino do arquivo MP3.")
            return

        self.presenter.on_start_requested(
            pages_expr=pages_expr,
            voice=voice,
            rate_percent=rate,
            out_path=Path(out_str),
            strategy_name=strat,
        )

    def _on_cancel_click(self) -> None:
        self.presenter.on_cancel_requested()

    # --- Implementação do DesktopView Protocol ---

    def set_state(self, state: UIState) -> None:
        is_working = state in {
            UIState.VALIDATING,
            UIState.EXTRACTING,
            UIState.NORMALIZING,
            UIState.SYNTHESIZING,
            UIState.FINALIZING,
        }
        self.btn_browse.configure(state="disabled" if is_working else "normal")
        self.btn_preview.configure(state="disabled" if is_working else "normal")
        self.btn_start.configure(state="disabled" if is_working else "normal")
        self.btn_cancel.configure(state="normal" if is_working else "disabled")

    def set_pdf_info(self, info: PDFInfo) -> None:
        has_text = "Sim" if info.has_text_layer else "Não"
        msg = f"Total: {info.page_count} página(s) | Camada de texto: {has_text}"
        self.lbl_pdf_info.configure(text=msg)
        if self.chk_all_pages_var.get():
            self.pages_entry.configure(state="normal")
            self.pages_entry.delete(0, "end")
            self.pages_entry.insert(0, f"1-{info.page_count}")
            self.pages_entry.configure(state="disabled")

    def set_output_path(self, path: Path) -> None:
        self.out_entry.delete(0, "end")
        self.out_entry.insert(0, str(path))

    def set_voices(self, voices: list[VoiceInfo], default_short_name: str) -> None:
        self._voices_cache = voices
        labels = [f"{v.short_name} ({v.friendly_name or v.gender or 'pt-BR'})" for v in voices]
        if labels:
            self.combo_voice.configure(values=labels)
            self.combo_voice.set(labels[0])

    def set_progress(self, fraction: float, message: str) -> None:
        self.progress_bar.set(max(0.0, min(1.0, fraction)))
        self.lbl_status.configure(text=message)

    def show_preview(self, preview: NarrationText) -> None:
        # Abre janela modal de prévia com abas Texto Bruto vs Normalizado
        win = ctk.CTkToplevel(self)
        win.title("Prévia do Texto - Matraca")
        win.geometry("750x550")
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(win)
        tabview.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        tab_norm = tabview.add("Texto Normalizado (para fala)")
        tab_orig = tabview.add("Texto Original Bruto")
        tab_stats = tabview.add("Estatísticas e Avisos")

        # Aba Normalizado
        tab_norm.grid_columnconfigure(0, weight=1)
        tab_norm.grid_rowconfigure(0, weight=1)
        txt_norm = ctk.CTkTextbox(tab_norm)
        txt_norm.grid(row=0, column=0, sticky="nsew")
        txt_norm.insert("1.0", preview.text)
        txt_norm.configure(state="disabled")

        # Aba Original
        tab_orig.grid_columnconfigure(0, weight=1)
        tab_orig.grid_rowconfigure(0, weight=1)
        txt_orig = ctk.CTkTextbox(tab_orig)
        txt_orig.grid(row=0, column=0, sticky="nsew")
        txt_orig.insert("1.0", preview.original_text)
        txt_orig.configure(state="disabled")

        # Aba Estatísticas
        tab_stats.grid_columnconfigure(0, weight=1)
        stats_box = ctk.CTkTextbox(tab_stats)
        stats_box.pack(fill="both", expand=True)
        stats_lines = [f"{k}: {v}" for k, v in preview.stats.items()]
        stats_lines.append(f"\nAvisos registrados: {len(preview.warnings)}")
        for w in preview.warnings:
            stats_lines.append(f" - {w}")
        stats_box.insert("1.0", "\n".join(stats_lines))
        stats_box.configure(state="disabled")

    def show_success(self, result: JobResult) -> None:
        kb = result.size_bytes / 1024
        msg = (
            f"Áudio gerado com sucesso!\n\n"
            f"Arquivo: {result.output_path.name}\n"
            f"Tamanho: {kb:.1f} KB\n"
            f"Duração aprox.: {result.estimated_duration_seconds:.1f} s"
        )
        messagebox.showinfo("Sucesso", msg)

    def show_error(self, message: str) -> None:
        messagebox.showerror("Erro", message)


def main() -> None:
    app = DesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
