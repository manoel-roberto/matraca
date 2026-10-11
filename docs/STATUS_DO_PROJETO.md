# Status do projeto

## Retomada rápida (máx. 25 linhas)
- Fase atual: 4 concluída (motor de áudio). Próxima: Fase 5 (Interface Desktop).
- Último commit/tag: `fase-4-concluida`
- Funciona (verificado por teste): seleção de páginas, extração, estratégias, normalização pura pt-BR em 9 etapas, motor de áudio assíncrono (edge-tts 7.2.8, FakeTTSBackend, chunking inteligente, escrita atômica de MP3 .part -> os.replace com validação mutagen, retentativas transitórias, cancelamento cooperativo, JobService facade completo, CLI mínima e diagnóstico doctor com --tts), 295 testes no total passando.
- Quebrado/pendente: interface Desktop (Fase 5) e interface Web (Fase 6).
- Decisões pendentes (com hipótese padrão): ver `docs/DECISOES_TECNICAS.md` (ADR-013 a ADR-015 registrados).
- PRÓXIMO PASSO EXATO: Fase 5 — Interface Desktop (CustomTkinter, presenter.py testável sem display, fila de eventos do worker, desktop_app.py).
- Comandos para validar: `scripts/check.sh` (usa `.venv`).

## Histórico por fase
### Fase 4 — Motor de áudio (2026-10-11)
- Concluído: `matraca/audio/` (chunking, mp3_writer, edge_tts_client, fake_tts), `matraca/core/audio_service.py`, `matraca/core/job_service.py`, `matraca/doctor.py`, `matraca/cli.py`, `docs/TESTE_MANUAL_TTS.md`, ADR-013 a ADR-015.
- Evidência: `scripts/check.sh` → ruff OK, mypy OK (40 arquivos), compileall OK, pytest → `295 passed in 4.67s`. Teste real do edge-tts executado com sucesso (3 vozes pt-BR, latência ~1012ms).
- Riscos/limitações: Nenhuma dependência de rede nos testes automatizados (usam FakeTTSBackend). Teste manual com edge-tts real registrado em `docs/TESTE_MANUAL_TTS.md`.
### Fase 3 — Pipeline de normalização (2026-10-11)
- Concluído: `matraca/text/` (linebreaks, numbers, dates, legal_terms, normalization), `matraca/core/text_pipeline.py`, `tests/golden/casos_normalizacao.tsv` (88 casos), invariantes, alinhamento de texto e métricas, `docs/EXEMPLOS_NORMALIZACAO.md`.
- Evidência: `scripts/check.sh` → ruff OK, mypy OK (31 arquivos), compileall OK, pytest → `258 passed in 2.82s`. ADR-011 e ADR-012 registrados.
- Riscos/limitações: nenhuma dependência de rede; casos de normalização cobrem 100% da tabela A.13.3 do prompt mestre.
### Fase 2 — Seleção de páginas e extração (2026-10-11)
- Concluído: `core/page_selection.py`, `pdf/pymupdf_reader.py`, `core/pdf_service.py`, `extractors/layout.py`, `extractors/noise.py`, `extractors/base.py`, `extractors/default.py`, `extractors/estrategia_concursos.py`, `extractors/registry.py`, fixtures sintéticas completas em `scripts/make_fixtures.py`.
- Evidência: `scripts/check.sh` → ruff OK, mypy OK (25 arquivos), compileall OK, pytest → `143 passed in 2.59s`. ADR-008, ADR-009 e ADR-010 registrados.
- Riscos/limitações: Sem PDFs reais fornecidos; padrões do Estratégia Concursos baseados em inferência e configuráveis em TOML.

### Fase 1 — Fundação e contratos (2026-10-11)
- Concluído: pacotes, `models`, `exceptions`, `progress`, `config`, `ports` (Protocols), `utils/paths`, `utils/logging_config`, `pyproject.toml`, `scripts/check.sh|.ps1`, esqueleto de `make_fixtures.py`.
- Evidência: `scripts/check.sh` → ruff check/format OK; compileall OK; mypy strict "no issues found in 16 source files"; `pytest` → `42 passed`.
- Riscos/limitações: `check.ps1` não pôde ser executado (sem Windows).

### Fase 0 — Inspeção, planejamento e riscos (2026-10-11)
- Concluído: git init; venv Python 3.12.13; dependências instaladas; documentos de controle.
- Evidência: ver "Ambiente" abaixo.
- Riscos/limitações: ver `PLANO_DE_IMPLEMENTACAO.md`.

## Ambiente (saídas reais)
- SO: Linux 6.8.0 x86_64 (Ubuntu 22.04). Python do sistema 3.10.12; usado `.venv` com 3.12.13 (uv 0.11.2).
- Rede: HTTP 200 em `https://pypi.org` (verificado).
- `ffmpeg`: `/usr/bin/ffmpeg` presente. `tkinter`: Tk 8.6 (sistema) / Tk 9.0 (venv). `DISPLAY=:0`. `xvfb-run`: ausente.
- PDFs reais: nenhum fornecido (`tests/fixtures/reais/` não existe) → padrões da Estratégia Concursos serão inferidos e configuráveis.

## Perguntas bloqueantes da Fase 0 e hipóteses adotadas (sem resposta → seguir)
1. PDFs reais do Estratégia Concursos? → **Não há**; usar fixtures sintéticas + regex configuráveis.
2. Python/SO alvo? → **Python ≥ 3.11 (dev em 3.12), Linux e Windows**.
3. Limite de upload na Web? → **50 MB** (`server.maxUploadSize`), configurável.
4. Incisos: cardinal ou ordinal? → **cardinal** (“inciso dois”), artigos 1–9 ordinal.
5. Rede disponível para teste real do TTS? → **sim, tentar na Fase 4**.
6. Aplicação de leitura de datas dd/mm/aaaa? → **sim**, só com dia/mês válidos.
