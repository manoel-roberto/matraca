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

## ADR-005 — Verificação de tipos com mypy (strict)
- Data / Fase: 2026-10-11 / Fase 1
- Decisão: `mypy --strict` em todo o pacote `matraca` (config no `pyproject.toml`); `ignore_missing_imports` apenas para `fitz`, `pymupdf`, `customtkinter`, `mutagen`.
- Evidência verificada: `mypy` → `Success: no issues found in 16 source files`.
- Status: aceita

## ADR-006 — Contratos em `core/ports.py` e modelos "crus" em `core/models.py`
- Data / Fase: 2026-10-11 / Fase 1
- Contexto: A.12.2 coloca `PDFTextStrategy` em `extractors/base.py`, mas `core/` (JobService) precisa do contrato sem importar adaptadores.
- Decisão: Protocols `PDFReader`, `PDFTextStrategy`, `TTSBackend` em `core/ports.py`; `extractors/base.py` os reexporta. O `PDFReader` devolve `RawPage/RawBlock/RawLine` (definidos em `core/models.py`), mantendo extratores independentes do PyMuPDF. `ProgressEvent`/`Stage` ficam em `core/progress.py` (evita ciclo).
- Alternativas consideradas: contrato dentro de `extractors/` (faria `core` depender de adaptadores).
- Consequências / riscos: pequeno desvio da árvore A.12.2 (um arquivo extra, `ports.py`).
- Status: aceita

## ADR-007 — Fronteiras de dependência verificadas por AST
- Data / Fase: 2026-10-11 / Fase 1
- Decisão: `tests/unit/test_architecture.py` impõe: `core/` só importa stdlib e `matraca.{core,config,text,audio.chunking}`; cada biblioteca de terceiros só é importada por seu adaptador; sem `eval/exec/shell=True`; `import matraca` sem efeitos.
- Evidência verificada: 5 testes passando (ver STATUS).
- Status: aceita

## ADR-008 — Seleção de páginas: ordem, separadores e Unicode
- Data / Fase: 2026-10-11 / Fase 2
- Contexto: A.13.1 exige decisões fixas e documentadas.
- Decisão: resultado **deduplicado e em ordem crescente**; separadores `,` e `;`; traços Unicode (– — ‑ ‐ − ‒) são **aceitos** e normalizados para `-`; zeros à esquerda aceitos (`007` = 7); dígitos não ASCII rejeitados; entrada vazia é erro; "todas" só por `PageSelection.all(total)`; números com mais de 9 dígitos rejeitados antes de qualquer conversão/expansão.
- Alternativas consideradas: preservar a ordem digitada (contraria A.13.1).
- Evidência verificada: 49 testes em `tests/unit/test_page_selection.py`.
- Status: aceita

## ADR-009 — Extração: ruído por múltiplos sinais, limiar 40% e padrões inferidos de Concursos
- Data / Fase: 2026-10-11 / Fase 2
- Contexto: A.13.2. Nenhum PDF real foi fornecido (Fase 0).
- Decisão: um bloco só é descartado com ≥ 2 sinais (`zona`, `repeticao`, `numeracao`, `rotacionado`, `claro`, `padrao`) ou numeração isolada na margem. Limiar de repetição padrão **40%** das páginas amostradas (mínimo 2 páginas), amostra de até 40 páginas distribuídas **entre as selecionadas**. Faixas: 10% topo/rodapé. "Claro" = alpha < 128 ou luminância em [0,75; 0,98) (branco puro é texto sobre faixa escura). Padrões de licenciamento/URL/bancas ficam em `matraca/extractors/concursos_patterns.toml` (**inferidos, não validados com PDFs reais**) e podem ser estendidos por `ExtractionConfig.extra_noise_patterns`. Formato `(BANCA/ANO)` só é reescrito para "Questão da banca X, de AAAA." se a sigla estiver na lista configurada.
- Alternativas consideradas: remover por posição (rejeitada: remove notas de rodapé legítimas).
- Evidência verificada: teste negativo com 4 notas de rodapé jurídicas na margem inferior (`test_nota_de_rodape_juridica_nao_e_removida`) e testes unitários de sinais isolados.
- Consequências / riscos: com 1 única página selecionada não há perfil de repetição (só numeração/rotação+claro/padrão funcionam). Padrões reais do Estratégia Concursos precisam de validação com PDFs reais.
- Status: aceita

## ADR-010 — API do PyMuPDF 1.28.2 verificada na instalação real
- Data / Fase: 2026-10-11 / Fase 2
- Evidência verificada (execução real): `pymupdf.open(path)` lança `FileDataError` (conteúdo inválido), `EmptyFileError` (0 byte) e `FileNotFoundError`; `doc.needs_pass` indica senha; `page.get_text("dict", flags=...)` devolve `blocks` (tipo 0 = texto com `lines`/`spans`: `dir`, `bbox`, `size`, `color`, `alpha`, `flags`; tipo 1 = imagem); `page.get_image_info()` dá bbox de imagens; `page.find_tables()` existe (`.tables[i].bbox`). Flag usada: `TEXT_MEDIABOX_CLIP` (sem preservar ligaduras/espaços repetidos). Ordem nativa dos blocos é a do fluxo de conteúdo; ordenamos por colunas em `extractors/layout.py`. `pymupdf.TOOLS.mupdf_display_errors(False)` silencia avisos do MuPDF no stderr (efeito global restrito ao módulo `pdf/pymupdf_reader.py`).
- Status: aceita

## ADR-011 — Pipeline de normalização e decisões linguísticas
- Data / Fase: 2026-10-11 / Fase 3
- Contexto: A.13.3 exige ordem fixa de etapas puras, integridade de conteúdo e decisões linguísticas registradas.
- Decisão: 
  1. Artigos até 9 são ordinais ("Artigo primeiro" a "Artigo nono"); a partir de 10 são cardinais ("Artigo dez", "Artigo trinta e sete").
  2. Parágrafos até 9 são ordinais ("parágrafo primeiro"); a partir de 10 são cardinais ("parágrafo dez"). "§ único" vira "parágrafo único".
  3. Incisos são cardinais ("inciso dois", "inciso dez") em dispositivos jurídicos ("inciso II" ou "II -"). Numerais romanos em monarcas ("Rei João II"), séculos ("Século XX") e capítulos ("Capítulo II") não viram incisos.
  4. Leis com barra são expandidas ("Lei 8.666/93" vira "Lei oito mil seiscentos e sessenta e seis, de noventa e três"). Casos ambíguos ("3/4", "2020/2021") são rigorosamente mantidos.
  5. Datas no formato dd/mm/aaaa têm o 1º dia lido como ordinal ("primeiro de...") e anos expandidos.
  6. Substrings como "Art." em "Martin", "Particular" ou "Cart." não sofrem substituição parcial.
  7. Ordem estrita das 9 etapas puras fixada e testada por invariante.
- Evidência verificada: 88 testes golden em `tests/golden/casos_normalizacao.tsv` aprovados com 100% de sucesso.
- Status: aceita

## ADR-012 — Conversão numérica com num2words 0.5.14 combinada com regras de domínio
- Data / Fase: 2026-10-11 / Fase 3
- Contexto: Avaliação entre biblioteca pronta e implementação própria (A.13.3).
- Decisão: Adotar `num2words` com `lang='pt_BR'` para cardinais, ordinais e moeda, isolada dentro de `matraca/text/numbers.py`. Camada própria para casos específicos do domínio jurídico (artigos 1-9 ordinais / 10+ cardinais, leis com barra, moeda "um milhão de reais", separadores decimais e de milhar).
- Alternativas consideradas: Implementação própria de cardinais até milhões (desnecessária com biblioteca instalada e verificada).
- Evidência verificada: Testes unitários de números, moeda e percentual passando.
- Status: aceita

## ADR-013 — Integração com edge-tts 7.2.8 e inspeção de API
- Data / Fase: 2026-10-11 / Fase 4
- Contexto: API do edge-tts precisa ser validada na instalação real (A.12.6, A.13.5).
- Decisão:
  1. `edge_tts.list_voices()` retorna dicionários contendo `ShortName`, `Locale`, `Gender` e `FriendlyName`. Filtrar por `Locale.startswith("pt-BR")`.
  2. `edge_tts.Communicate(text, voice, rate=rate)` aceita `rate` no formato string percentual (`+0%`, `+20%`, `-10%`).
  3. `Communicate.save(dest)` assíncrono grava diretamente em arquivo.
  4. Isolar chamadas de edge-tts no adaptador `matraca/audio/edge_tts_client.py` implementando o Protocol `TTSBackend`.
  5. Testes automatizados nunca chamam o edge-tts real; usam `FakeTTSBackend` (`audio/fake_tts.py`).
- Evidência verificada: Inspeção direta no Python 3.12 (`edge-tts 7.2.8`), identificando 3 vozes pt-BR ativas (`pt-BR-ThalitaMultilingualNeural`, `pt-BR-AntonioNeural`, `pt-BR-FranciscaNeural`).
- Status: aceita

## ADR-014 — Concatenação direta de segmentos MP3 e validação com Mutagen
- Data / Fase: 2026-10-11 / Fase 4
- Contexto: Avaliação entre concatenação de fluxo MP3 puro vs FFmpeg/pydub para junção de áudios (A.13.5).
- Decisão:
  1. Utilizar concatenação binária direta de streams MP3 gerados pelo mesmo serviço/voz através da interface `Mp3Joiner`.
  2. Validar o arquivo concatenado final utilizando `mutagen.mp3.MP3` (inspecionando cabeçalhos MPEG, bitrate e duração positiva).
  3. Evitar dependência obrigatória de subprocesso do FFmpeg em tempo de execução para a junção básica de MP3 homogêneos.
- Evidência verificada: Spike técnico real com 2 segmentos gerados pelo edge-tts unidos diretamente e validados com `mutagen.mp3.MP3(joined)`, resultando em 5.496s de áudio decodificável sem erros.
- Status: aceita

## ADR-015 — Concorrência e ciclo de vida de Jobs (Thread isolada com Event Loop próprio)
- Data / Fase: 2026-10-11 / Fase 4
- Contexto: Orquestração de tarefas assíncronas do TTS sem conflitar com loops ativos de UIs (A.12.7).
- Decisão:
  1. `JobService` executa o processamento do job em uma `threading.Thread` dedicada de trabalho.
  2. A thread de trabalho inicializa e encerra seu próprio `asyncio.new_event_loop()`, garantindo que nunca ocorra colisão de `asyncio.run()` com loops existentes de frameworks (como Streamlit ou CustomTkinter).
  3. Progresso e cancelamento via `ProgressCallback` e `CancellationToken` (thread-safe baseados em `threading.Event`).
- Evidência verificada: Testes de concorrência com `FakeTTSBackend` simulando cancelamento precoce e falhas progressivas.
- Status: aceita

## ADR-016 — Padrão MVP para Interface Desktop e comunicação via Fila Thread-Safe
- Data / Fase: 2026-10-11 / Fase 5
- Contexto: A interface gráfica Desktop (CustomTkinter) precisa ser 100% testável de forma determinística sem exigir monitor/display ativo (headless) e nunca bloquear a thread de renderização da UI (A.13.6, RNF-07).
- Decisão:
  1. Adotar o padrão Model-View-Presenter (MVP).
  2. O `DesktopPresenter` gerencia todo o estado da UI, validações de entrada e orquestração de tarefas assíncronas do `JobService`, implementando lógica pura em Python sem qualquer importação de `customtkinter` ou `tkinter`.
  3. A comunicação dos trabalhadores em segundo plano (extração, prévia, síntese) para a thread da UI ocorre através de uma fila thread-safe `queue.Queue`.
  4. A View concreta (`DesktopApp`) apenas consome os eventos da fila através de agendamento periódico com `root.after(50, presenter.poll_events)`, garantindo que nenhum widget seja modificado fora da thread principal de eventos da UI.
- Evidência verificada: Testes unitários com `FakeView` cobrindo seleção de PDF, prévia, validação, fluxo de execução, erro, cancelamento e nova tentativa executam sem display em milissegundos.
- Status: aceita

## ADR-017 — Interface Web com Streamlit, isolamento de sessão e sanitização de uploads
- Data / Fase: 2026-10-11 / Fase 6
- Contexto: A interface Web deve permitir upload, prévia, geração de áudio e download com segurança de dados, isolamento de sessão, respeito ao modelo de reexecução do Streamlit e sem duplicação de lógica de domínio (A.13.7, RF-16).
- Decisão:
  1. Extrair toda a lógica de validação de uploads, sanitização de caminhos, formatação de taxas e gerenciamento de temporários para `matraca/web/page_logic.py`, isolada de dependências visuais e testável de forma unitária.
  2. A validação de arquivos enviados verifica tamanho máximo (configurado em 50 MB via `.streamlit/config.toml` e `MAX_UPLOAD_MB_DEFAULT`), sanitiza rigorosamente o nome do arquivo com `sanitize_filename` e valida o cabeçalho mágico de PDF (`%PDF-` nos primeiros 1024 bytes).
  3. Os arquivos são isolados por sessão através do `WebSessionManager` em pastas temporárias exclusivas sob o diretório temporário do sistema, sendo removidos no descarte/reinicialização.
  4. A execução da síntese de áudio reutiliza o mesmo `JobService` central das demais interfaces, executando o job através de `JobService.run_job_in_thread(...)` com sincronização via fila thread-safe e atualização reativa de progresso no Streamlit.
- Evidência verificada: Testes unitários em `tests/unit/test_web_logic.py` cobrem validação de nomes maliciosos, detecção de cabeçalho mágico, rejeição de limites de tamanho, ciclo de vida dos temporários, integração com `JobService` e teste de montagem visual via `streamlit.testing.v1.AppTest`.
- Status: aceita

## Decisões a tomar nas fases seguintes
- ADR: empacotamento, testes de longa duração e validação de regressão (Fase 7).

