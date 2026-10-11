# Arquitetura

## Camadas

```mermaid
flowchart TD
    subgraph Interfaces
        GUI[gui: CustomTkinter + Presenter]
        WEB[web: Streamlit]
        CLI[cli / doctor]
    end
    GUI --> JOB
    WEB --> JOB
    CLI --> JOB
    subgraph Core[core: serviços e contratos]
        JOB[JobService]
        PDFS[pdf_service]
        PIPE[text_pipeline]
        AUD[audio_service]
        PSEL[page_selection]
    end
    JOB --> PDFS & PIPE & AUD & PSEL
    PDFS -. Protocol PDFReader .-> PYMU[pdf/pymupdf_reader]
    JOB -. Protocol PDFTextStrategy .-> EXT[extractors/*]
    AUD -. Protocol TTSBackend .-> EDGE[audio/edge_tts_client]
    PIPE --> TXT[text/*: etapas puras]
    AUD --> CHK[audio/chunking, mp3_writer]
```

## Regras
- `core/` não importa `gui`, `web`, `streamlit`, `customtkinter`, `edge_tts` nem `fitz` (teste AST na Fase 1).
- Interfaces chamam apenas `JobService`.
- Configuração por `dataclass(frozen=True)`; sem estado global mutável.

## Fluxo de dados
PDF → `PDFReader` → `PDFTextStrategy.extract` (`ExtractionResult`) → `text_pipeline` (`NarrationText`) → `chunking` → `TTSBackend` (segmento a segmento, em temporário) → `Mp3Joiner` → escrita atômica `.part` → `os.replace` → validação.

## Ordem das etapas de normalização
(definida e fixada por teste na Fase 3)

## Concorrência
(definida em ADR na Fase 4)
