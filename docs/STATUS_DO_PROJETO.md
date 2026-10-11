# Status do projeto

## Retomada rápida (máx. 25 linhas)
- Fase atual: 2 concluída (seleção de páginas e extração). Próxima: Fase 3.
- Último commit/tag: `fase-2-concluida`
- Funciona (verificado por teste): modelos, exceções, progresso/cancelamento, utils/paths, seleção de páginas (49 testes), PyMuPDFReader, PDFService, estratégias Default e Concursos com TOML configurável, remoção de ruído por múltiplos sinais, ordem de leitura em colunas, testes de integração sintéticos (143 testes no total).
- Quebrado/pendente: normalização (Fase 3), áudio (Fase 4), UIs (Fases 5 e 6).
- Decisões pendentes (com hipótese padrão): ver `docs/DECISOES_TECNICAS.md` (ADR-008 a ADR-010 registrados).
- PRÓXIMO PASSO EXATO: Fase 3 — Pipeline de normalização para narração pt-BR (`text/`, golden tests com ≥ 80 casos, invariantes, `docs/EXEMPLOS_NORMALIZACAO.md`).
- Comandos para validar: `scripts/check.sh` (usa `.venv`).

## Histórico por fase
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
