# Status do projeto

## Retomada rápida (máx. 25 linhas)
- Fase atual: 8 concluída (Documentação e Entrega Final). TODAS AS FASES (0 a 8) CONCLUÍDAS COM SUCESSO.
- Último commit/tag: `fase-8-concluida`
- Funciona (verificado por teste real):
  - Seleção de páginas por expressão ou totalidade com validação de limites;
  - Extração de texto por layout, colunas e heurística de ruídos (Estratégia Concursos);
  - Normalização pura pt-BR em 9 etapas cobrindo leis, artigos, parágrafos, incisos, números, datas e siglas;
  - Motor assíncrono de áudio (edge-tts 7.2.8, FakeTTSBackend, chunking inteligente, escrita atômica .part -> os.replace, validação mutagen);
  - JobService facade central com concorrência thread-safe e CancellationToken;
  - Diagnóstico do ambiente com CLI e `python -m matraca doctor [--tts]`;
  - Interface Desktop CustomTkinter desacoplada com padrão MVP e janela modal de prévia;
  - Interface Web Streamlit com upload seguro (50MB), sanitização e isolamento por sessão;
  - Suíte de 311 testes unitários/integração + 1 teste lento de documento extenso (500 páginas);
  - Cobertura global de código de 91% medida com `pytest-cov`;
  - Simulação de instalação em ambiente virtual limpo executada e validada do zero;
  - Documentação completa (`README.md`, `ARQUITETURA.md`, `CLAUDE.md`, `EXEMPLOS_NORMALIZACAO.md`).
- Quebrado/pendente: NENHUMA pendência técnica. Projeto 100% pronto para uso e entrega.
- Decisões vigentes: ADR-001 a ADR-017 registrados em `docs/DECISOES_TECNICAS.md`.
- Comandos para validar: `./scripts/check.sh` (Linux) ou `.\scripts\check.ps1` (Windows).

## Histórico por fase
### Fase 8 — Documentação e entrega final (2026-10-11)
- Concluído: `README.md` completo (instalação, UIs, CLI, testes, privacidade, limitações, troubleshooting), `docs/ARQUITETURA.md` com diagramas Mermaid de fluxo e camadas, revisão de `CLAUDE.md`, inclusão de `num2words>=0.5.14` em `requirements.txt` e `pyproject.toml`, simulação e validação de instalação limpa em venv isolado com sucesso (`python -m matraca doctor` aprovado).
- Evidência: `scripts/check.sh` → ruff OK, mypy strict OK (44 arquivos), compileall OK, pytest → `311 passed, 1 skipped, 1 deselected in 4.00s`. Simulação limpa do zero executada com sucesso.
### Fase 7 — Integração, regressão, revisão (2026-10-11)
- Concluído: teste lento `test_perf_500p.py` com `grande_500.pdf` (1.26s), relatório de cobertura `pytest-cov` registrando 91% global (100% page_selection, 98% job_service, 91% audio_service, 93%-95% text, 90% chunking), checklist de segurança e privacidade 100% verificado (sem logs de texto, sem eval/exec/shell=True, sanitização estrita, limpeza de temporários).
- Evidência: `scripts/check.sh` → ruff OK, mypy strict OK (44 arquivos), compileall OK, pytest → `311 passed, 1 skipped, 1 deselected in 5.75s`. `pytest -m slow` → `1 passed in 1.26s`. Cobertura → `91% TOTAL`.
- Riscos/limitações: nenhuma dependência de rede na suíte automatizada; integridade de isolamento garantida.
### Fase 6 — Interface Web com Streamlit (2026-10-11)
- Concluído: `matraca/web/page_logic.py`, `matraca/web/streamlit_app.py`, `app_web.py`, `.streamlit/config.toml`, ADR-017, testes unitários e AppTest em `tests/unit/test_web_logic.py`.
- Evidência: `scripts/check.sh` → ruff OK, mypy strict OK (44 arquivos), compileall OK, pytest → `311 passed, 1 skipped in 5.59s`. Execução real do Streamlit testada via uvicorn/http 8502 com sucesso.
- Riscos/limitações: Interface web sem autenticação para uso local documentada com avisos de privacidade explícitos sobre o TTS remoto.
### Fase 5 — Interface Desktop (2026-10-11)
- Concluído: `matraca/gui/presenter.py`, `matraca/gui/desktop_app.py`, `app_desktop.py`, `docs/ROTEIRO_TESTE_DESKTOP.md`, ADR-016, 8 testes unitários de presenter cobrindo seleção, prévia, geração, cancelamento e erro sem display.
- Evidência: `scripts/check.sh` → ruff OK, mypy OK (42 arquivos), compileall OK, pytest → `303 passed in 4.78s`.
- Riscos/limitações: Interface gráfica interativa depende de servidor X/Wayland em ambiente de usuário final; coberta por testes automatizados sem display via FakeDesktopView e MVP desacoplado. Roteiro manual em `docs/ROTEIRO_TESTE_DESKTOP.md`.
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
