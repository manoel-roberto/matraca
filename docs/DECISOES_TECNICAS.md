# Decisões técnicas (ADRs)

## ADR-001 — Estrutura de diretórios e camadas
- Data / Fase: 2026-10-11 / Fase 0
- Contexto: A.12.1 e A.12.2 do prompt mestre definem camadas e árvore inicial.
- Decisão: adotar a árvore da A.12.2 sem alterações. Dependências apontam para dentro; `core/` só usa Protocols.
- Alternativas consideradas: monorepo com pacotes separados por interface (complexidade desnecessária).
- Evidência verificada: diretório estava vazio (apenas `Prompt_Matraca_v2.md`).
- Consequências / riscos: arquivos pequenos exigem disciplina de divisão.
- Status: aceita

## ADR-002 — Python alvo 3.12 (via uv), mínimo suportado 3.11
- Data / Fase: 2026-10-11 / Fase 0
- Contexto: o Python do sistema é 3.10.12 (`python3 --version`); o prompt exige 3.11+. `uv 0.11.2` está disponível.
- Decisão: `.venv` com CPython 3.12.13 instalado por `uv python install 3.12`. `requires-python = ">=3.11"`. Verificado: todas as dependências instalaram e `tkinter` (Tk 9.0) importa nesse Python.
- Alternativas consideradas: 3.14 (já instalado via uv; menos testado pelas dependências científicas como numpy/pandas do Streamlit), 3.10 do sistema (abaixo do exigido).
- Evidência verificada: `uv pip install ...` concluiu sem erro; `.venv/bin/python -c "import tkinter"` → `tk ok 9.0`.
- Consequências / riscos: usuários precisam de Python ≥ 3.11 (documentar `uv`/`python.org`).
- Status: aceita

## ADR-003 — Padrão de nomes: identificadores em inglês; docstrings, comentários e mensagens em pt-BR
- Data / Fase: 2026-10-11 / Fase 0
- Contexto: A.13.9 exige escolher um padrão único e registrá-lo. A.12.4 já prescreve exceções em português (`PDFInvalidoError`...) e módulos como `estrategia_concursos`.
- Decisão: identificadores de código em inglês (funções, variáveis, classes de modelos), **exceto** os nomes explicitamente prescritos pelo prompt (exceções `*Error` em português, `estrategia_concursos.py`, campo `rate` etc.). Docstrings, comentários, logs de usuário e mensagens em pt-BR.
- Alternativas consideradas: tudo em português (conflita com nomes de bibliotecas e Protocols).
- Evidência verificada: n/a (convenção).
- Consequências / riscos: pequena mistura inevitável, restrita aos nomes prescritos.
- Status: aceita

## ADR-004 — Dependências iniciais (versões instaladas e verificadas)
- Data / Fase: 2026-10-11 / Fase 0
- Contexto: A.13.11 exige versões verificadas via `pip install` real.
- Decisão: PyMuPDF 1.28.2, edge-tts 7.2.8, customtkinter 6.0.0, streamlit 1.65.0, mutagen 1.48.1 (validação de MP3), num2words 0.5.14 (a confirmar na Fase 3). Dev: pytest 9.1.1, pytest-cov 7.1.0, ruff 0.17.0, mypy 2.4.0.
- Alternativas consideradas: pyright (exige Node); pydub (exige FFmpeg; decidir na Fase 4).
- Evidência verificada: `uv pip freeze` (saída acima, filtrada).
- Consequências / riscos: versões muito recentes podem mudar APIs; cada API será inspecionada antes do uso (A.1).
- Status: aceita (num2words: proposta até a Fase 3)

## ADR-005 — Verificação de tipos com mypy
- Data / Fase: 2026-10-11 / Fase 0
- Decisão: mypy em modo estrito moderado para `core/`, `text/`, `audio/`; demais pacotes com checagem padrão.
- Status: proposta (confirmar na Fase 1)

## Decisões a tomar nas fases seguintes
- ADR: ordem das páginas — crescente e deduplicada (Fase 2; fixa pelo prompt A.13.1).
- ADR: limiar de repetição de ruído (padrão 40%) (Fase 2).
- ADR: leitura de incisos (cardinal × ordinal), artigos ≤ 9 ordinal, siglas, `num2words` × própria (Fase 3).
- ADR: concorrência, tamanho do chunk, `rate`, junção de MP3, inspeção do `edge-tts` (Fase 4).
- ADR: MVP da GUI (Fase 5); estado Streamlit (Fase 6).
