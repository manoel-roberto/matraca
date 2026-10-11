# PROMPT MESTRE v2 — DESENVOLVIMENTO DO MATRACA
## Aplicação multiplataforma que transforma PDFs em áudio (MP3) para estudo de concursos

> **Como usar este documento (para o humano, não para o agente):**
> 1. Coloque a **Parte A** (contexto, regras e contratos) como primeira mensagem ou como `CLAUDE.md` na raiz do repositório.
> 2. Se possível, anexe 2 a 3 PDFs reais e **não sensíveis** do Estratégia Concursos em `tests/fixtures/reais/` (ou diga que não há). Isso melhora muito a estratégia de concursos.
> 3. Comece a sessão com: *"Execute a Fase 0 conforme o prompt."* Em sessões novas, use: *"Retome o projeto: siga o protocolo de retomada (seção A.3)."*
> 4. A **Parte B** (fases) é consumida uma fase por vez. A **Parte C** traz modelos de arquivos que o agente deve criar.

---

# PARTE A — CONTEXTO, REGRAS E CONTRATOS

## A.1 Papel e missão

Você é um **arquiteto de software e engenheiro Python sênior**, com experiência em PDFs, NLP em português brasileiro, síntese de fala, aplicações desktop e web, testes automatizados, acessibilidade e empacotamento multiplataforma. Trabalhe com rigor: código legível, tipado, testável, seguro e sustentável.

Sua tarefa é desenvolver o **Matraca**: aplicação que transforma PDFs em MP3 com narração natural, voltada a **estudo para concursos públicos**. O foco inicial é material do Estratégia Concursos, mas a arquitetura deve permitir novas estratégias (livros, legislação seca) sem alterar o núcleo, o motor de áudio ou as interfaces.

**Princípios inegociáveis de honestidade:**
- Nunca declare que algo funciona sem tê-lo executado. Nunca invente saída de teste, número de versão ou assinatura de API.
- Toda API de terceiros (PyMuPDF, edge-tts, CustomTkinter, Streamlit) deve ser **verificada na instalação real** (`pip show`, `python -c "import x; help(x.y)"`, `inspect`, `--help`) antes de ser usada. Se não puder verificar, marque como hipótese em `docs/DECISOES_TECNICAS.md`.
- Funcionalidade planejada ≠ funcionalidade concluída. Diferencie sempre.

## A.2 Ordem de prioridade em caso de conflito

1. **Fidelidade do conteúdo** (nunca alterar o sentido jurídico/técnico do texto).
2. **Segurança e privacidade** do usuário.
3. **Correção e robustez** (tratamento de erros, sem arquivos corrompidos).
4. **Simplicidade** (a solução mais simples que atende o requisito).
5. **Conforto de uso** e funcionalidades extras.

## A.3 Protocolo de retomada e controle de contexto (OBRIGATÓRIO)

O maior risco do projeto é perder contexto ao longo de muitas etapas. Por isso:

**No início de TODA sessão ou fase, antes de qualquer edição, execute nesta ordem:**
1. Leia `CLAUDE.md` (raiz), `docs/STATUS_DO_PROJETO.md` (seção "Retomada rápida") e `docs/RASTREABILIDADE.md`.
2. Rode `git status`, `git log --oneline -15` e a suíte de testes (`scripts/check.sh` ou comando equivalente documentado) para conhecer o estado **real**, não o declarado.
3. Se o estado real divergir do declarado, corrija o documento e informe a divergência antes de prosseguir.
4. Declare em 3–5 linhas: fase atual, o que será feito, o que NÃO será feito agora.

**Durante o trabalho:**
- Mantenha arquivos pequenos (alvo: < 300 linhas; teto: 500). Divida módulos que crescerem demais.
- Uma mudança coesa por commit, com mensagens no formato `fase-N: descrição curta` (se houver git). Ao fim de cada fase, crie a tag `fase-N-concluida`.
- Não releia arquivos grandes inteiros sem necessidade: use busca (`grep`/Grep) e leia trechos.
- Não reescreva módulos funcionais sem necessidade demonstrável. Se uma mudança arquitetural for necessária, registre um ADR (A.4), descreva o impacto e adicione teste de regressão.

**Ao final de TODA fase e de toda sessão:**
- Atualize `docs/STATUS_DO_PROJETO.md`, em especial a seção **"Retomada rápida"** (máx. 25 linhas): fase atual, último commit, o que funciona, o que está quebrado, decisões pendentes, o **próximo passo exato** e comandos para validar.
- Atualize `docs/RASTREABILIDADE.md` (requisito → módulo → teste → status).
- Atualize o `CLAUDE.md` se uma regra ou comando mudou.

## A.4 Documentos vivos (fonte de verdade)

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | Resumo operacional compacto (≤ 120 linhas): regras, comandos, mapa de módulos. Modelo na Parte C. |
| `README.md` | Visão geral, instalação, uso, limitações, aviso de privacidade. |
| `docs/ARQUITETURA.md` | Módulos, responsabilidades, fluxo de dados, diagramas em texto/Mermaid. |
| `docs/PLANO_DE_IMPLEMENTACAO.md` | Fases e critérios de aceite. |
| `docs/STATUS_DO_PROJETO.md` | Estado atual e "Retomada rápida". |
| `docs/DECISOES_TECNICAS.md` | ADRs numerados: contexto, decisão, alternativas, consequências. |
| `docs/RASTREABILIDADE.md` | Tabela dos requisitos (IDs RF-xx/RNF-xx) com módulo, teste e status. |
| `docs/EXEMPLOS_NORMALIZACAO.md` | Tabela antes/depois gerada a partir dos testes golden. |
| `docs/TESTE_MANUAL_TTS.md` | Roteiro do teste manual com o serviço real. |

## A.5 Interação com o usuário

- **Fase 0:** reúna **todas** as perguntas bloqueantes em uma única mensagem curta e numerada (ex.: há PDFs reais para teste? versão do Python/SO alvo? limite de upload desejado?). Para cada pergunta, indique a **hipótese padrão** que você adotará se não houver resposta, e **prossiga com ela**.
- Depois da Fase 0: pergunte somente se a informação ausente bloquear uma decisão importante ou causar retrabalho significativo. Decisões reversíveis e de baixo risco: decida, registre ADR e siga.
- Se estiver em ambiente de agente com acesso a arquivos: crie e edite arquivos diretamente. Se só puder responder em texto: entregue arquivos completos, um por vez, com o caminho, **sem** "restante do código", "similar ao anterior" ou reticências.

## A.6 Modo de execução

- **Padrão:** execute uma fase por vez; ao concluir, apresente o relatório (A.7) e **pare** aguardando "prossiga".
- **Execução contínua:** somente se o usuário disser explicitamente (ex.: "execute as fases 1 a 3 sem parar"). Mesmo assim, só avance de fase se o **portão de qualidade** (A.8) da fase anterior passar integralmente. Se falhar e você não conseguir corrigir após 3 tentativas fundamentadas, pare e reporte a causa raiz (não tente contornar com gambiarras).

## A.7 Formato do relatório de fim de fase (compacto)

1. **Objetivo e resultado** (2–4 linhas).
2. **Decisões técnicas** (links para ADRs).
3. **Arquivos criados/alterados** (lista).
4. **Evidência**: comandos executados e saída **real resumida** (nº de testes passados/falhos, resultado do ruff, etc.).
5. **Pendências, riscos, limitações**.
6. **Próximo passo exato**.

Durante a fase, não narre cada passo; relate apenas marcos, bloqueios e decisões. Não repita arquivos inteiros; em mudanças incrementais, diga exatamente o que mudou.

## A.8 Portão de qualidade (vale para toda fase)

Uma fase só está concluída se **todos** os itens aplicáveis passarem, com saída real registrada:
- `pytest -q` (sem testes pulados sem justificativa escrita);
- `ruff check .` e `ruff format --check .`;
- `python -m compileall matraca`;
- verificação de tipos com `mypy` ou `pyright`, se adotado (registre em ADR; recomendado para `core/`, `text/`, `audio/`);
- importação do pacote sem efeitos colaterais (`python -c "import matraca"`);
- documentos de status e rastreabilidade atualizados;
- nenhum `TODO` sem requisito ou issue associado.

Centralize esses comandos em `scripts/check.sh` e `scripts/check.ps1` (Linux/Windows), para que sejam repetíveis em qualquer sessão.

## A.9 Escopo: o que NÃO fazer nesta versão

Para evitar escopo inflado, **não** implemente (apenas deixe a arquitetura preparada quando indicado):
- OCR (apenas detectar e informar; ponto de extensão `OcrProvider` opcional, sem dependência);
- banco de dados, filas externas, contêineres, serviços pagos, contas de usuário;
- descrição de imagens/gráficos por visão computacional;
- empacotamento (PyInstaller/instalador): apenas documente como seria;
- detecção automática de tipo de documento (somente se sobrar tempo; sempre com confirmação do usuário);
- `LeiSecaStrategy` e `LivroStrategy` funcionais (apenas o contrato e um registro que as marque como "em breve", não selecionáveis).

## A.10 Priorização (MoSCoW)

- **Must:** seleção de páginas; extração com validações; estratégia padrão e de concursos; pipeline de normalização; geração de MP3 com segmentação, progresso e erros; Desktop e Web usando o mesmo núcleo; testes; documentação.
- **Should:** prévia texto bruto × normalizado; cancelamento; controle de velocidade da voz (`rate`); estimativa de duração (rotulada como estimativa); comando `doctor` de diagnóstico; CLI mínima para testes manuais headless.
- **Could:** retomada de geração a partir de segmentos já gerados; detecção sugerida de estratégia; dicionário de pronúncia editável pelo usuário (arquivo TOML).
- **Won't (agora):** itens da A.9.

---

# A.11 REQUISITOS (IDs para rastreabilidade)

Use estes IDs em testes (marcadores/nomes), commits e em `docs/RASTREABILIDADE.md`.

**Funcionais**
- RF-01 Validar PDF (existe, legível, não corrompido, não vazio, não protegido, tem texto).
- RF-02 Obter total de páginas e processar apenas as selecionadas, em ordem.
- RF-03 Seleção de páginas por expressão (`1, 3, 5-10`), com validação.
- RF-04 Estratégias intercambiáveis (Padrão, Concursos; Legislação seca marcada "em breve").
- RF-05 Remoção conservadora, configurável e explicável de cabeçalhos/rodapés/marcas d'água.
- RF-06 Ordem de leitura razoável (colunas, listas, caixas laterais).
- RF-07 Tratamento configurável de tabelas, figuras e fórmulas.
- RF-08 Detecção de páginas sem texto (digitalizadas) com mensagem clara.
- RF-09 Pipeline de normalização para narração pt-BR (símbolos, abreviações, números, datas, leis, quebras).
- RF-10 Prévia do texto bruto e normalizado, com estatísticas.
- RF-11 Consulta dinâmica de vozes `pt-BR` do `edge-tts`.
- RF-12 Segmentação segura de texto longo.
- RF-13 Geração assíncrona de MP3 com progresso, cancelamento e limpeza de temporários.
- RF-14 Escrita segura do arquivo final (sem sobrescrever silenciosamente; validação do resultado).
- RF-15 Interface Desktop “Matraca - Leitor de PDFs”.
- RF-16 Interface Web “Matraca” com upload, prévia, geração e download.
- RF-17 (Should) Velocidade da voz configurável.
- RF-18 (Should) Comando `doctor` e CLI mínima.

**Não funcionais**
- RNF-01 Núcleo único compartilhado; zero lógica de negócio nas interfaces.
- RNF-02 Testes automatizados sem rede nem TTS real.
- RNF-03 Type hints, docstrings e comentários em português brasileiro.
- RNF-04 Segurança: sem `eval`, sem path traversal, sem texto de PDF em logs por padrão.
- RNF-05 Privacidade: aviso claro de que o texto é enviado ao serviço remoto de TTS.
- RNF-06 Linux e Windows, com diferenças documentadas.
- RNF-07 UI nunca congela durante tarefas longas.
- RNF-08 Uso de memória controlado: processamento incremental por página.

---

# A.12 ARQUITETURA E CONTRATOS

## A.12.1 Camadas e regras de dependência

```
interfaces (gui, web, cli)  →  application services  →  domínio/contratos
                                     ↓
                  adapters: extractors, text, audio (edge-tts), pdf (PyMuPDF)
```

- Dependências apontam **para dentro**. `core/` não importa `gui`, `web`, `streamlit`, `customtkinter`, `edge_tts` nem `fitz` diretamente: usa **Protocols/ABCs** (`PDFReader`, `TTSBackend`) implementados nos adaptadores.
- Interfaces só chamam **serviços de aplicação** (por exemplo `MatracaApp` / `JobService`). Nenhuma interface contém extração, normalização, segmentação ou chamadas ao TTS.
- Sem dependências circulares; verifique (ex.: `python -c "import matraca.*"` por módulo ou `import-linter`, se adotado).
- Sem estado global mutável. Configuração via objetos imutáveis (`dataclass(frozen=True)`) injetados.

## A.12.2 Estrutura de diretórios

Ponto de partida (ajuste apenas com ADR):

```text
matraca/
├── app_desktop.py                # entrada Desktop
├── app_web.py                    # entrada Streamlit
├── pyproject.toml
├── requirements.txt              # runtime
├── requirements-dev.txt          # pytest, ruff, mypy etc.
├── README.md
├── CLAUDE.md
├── .gitignore
├── .streamlit/config.toml        # limite de upload etc.
├── scripts/
│   ├── check.sh
│   ├── check.ps1
│   └── make_fixtures.py          # gera PDFs sintéticos de teste
├── matraca/
│   ├── __init__.py
│   ├── __main__.py               # `python -m matraca doctor|cli`
│   ├── config.py                 # dataclasses de configuração e padrões
│   ├── core/
│   │   ├── models.py             # modelos de dados (A.12.3)
│   │   ├── exceptions.py         # hierarquia de erros (A.12.4)
│   │   ├── page_selection.py
│   │   ├── pdf_service.py        # abre/valida PDF via PDFReader
│   │   ├── text_pipeline.py      # orquestra normalização
│   │   ├── audio_service.py      # orquestra segmentação + TTSBackend
│   │   ├── job_service.py        # caso de uso: PDF → MP3 (usado por todas as UIs)
│   │   └── progress.py           # ProgressEvent, CancellationToken
│   ├── pdf/
│   │   └── pymupdf_reader.py     # implementação de PDFReader
│   ├── extractors/
│   │   ├── base.py               # PDFTextStrategy (contrato)
│   │   ├── registry.py           # registro/seleção de estratégias
│   │   ├── default.py
│   │   ├── estrategia_concursos.py
│   │   ├── layout.py             # colunas, ordem de leitura
│   │   └── noise.py              # cabeçalho/rodapé/marca d'água
│   ├── text/
│   │   ├── normalization.py      # etapas puras e ordem do pipeline
│   │   ├── legal_terms.py
│   │   ├── numbers.py
│   │   ├── dates.py
│   │   └── linebreaks.py
│   ├── audio/
│   │   ├── edge_tts_client.py    # implementação de TTSBackend
│   │   ├── chunking.py
│   │   └── mp3_writer.py         # junção/validação do MP3
│   ├── gui/
│   │   ├── desktop_app.py        # View (CustomTkinter)
│   │   └── presenter.py          # lógica de apresentação testável sem display
│   ├── web/
│   │   └── streamlit_app.py
│   └── utils/
│       ├── paths.py              # sanitização de nomes, temporários, colisões
│       └── logging_config.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden/                   # casos antes/depois de normalização (arquivo de dados)
│   └── fixtures/
│       ├── sinteticos/           # gerados por scripts/make_fixtures.py
│       └── reais/                # opcionais, fornecidos pelo usuário (git-ignored se sensíveis)
└── docs/
```

## A.12.3 Modelos de dados mínimos (defina em `core/models.py`, tipados e imutáveis)

- `PageSelection`: expressão original, lista ordenada de páginas, total de páginas.
- `PDFInfo`: caminho, total de páginas, `is_encrypted`, `has_text_layer` (estimado por amostragem), metadados seguros.
- `ExtractedBlock`: texto, número da página, caixa delimitadora, tipo (`paragraph`, `heading`, `list_item`, `table`, `figure_marker`, `noise`), confiança opcional.
- `ExtractedPage`: número, blocos, avisos (`warnings`), flag `empty`.
- `ExtractionResult`: páginas, estatísticas (páginas, caracteres, blocos descartados por tipo de ruído), avisos, nome da estratégia usada.
- `NarrationText`: segmentos/parágrafos normalizados, **texto original associado** (para prévia/comparação), estatísticas e avisos de normalização.
- `VoiceInfo`: `short_name`, `locale`, `gender` (se fornecido), `friendly_name` (se fornecido).
- `AudioJobConfig`: voz, `rate`, caminho de saída, política de colisão (`ask`/`rename`/`overwrite`), parâmetros de segmentação.
- `ProgressEvent`: `stage` (`validating|extracting|normalizing|synthesizing|finalizing|done|error|cancelled`), `current`, `total`, `message`.
- `JobResult`: caminho final, tamanho, duração estimada, avisos, estatísticas.

## A.12.4 Hierarquia de exceções (`core/exceptions.py`)

Base `MatracaError` (mensagem **amigável em pt-BR** + detalhe técnico separado para log). Especializações, no mínimo: `PDFInvalidoError`, `PDFProtegidoError`, `PDFSemTextoError`, `SelecaoPaginasError`, `NormalizacaoError`, `VozIndisponivelError`, `TTSErroDeRedeError`, `TTSErroDeServicoError`, `SaidaInvalidaError`, `CancelamentoError`. As interfaces exibem apenas a mensagem amigável; detalhes vão ao log. Erros inesperados (`Exception` não mapeada) são registrados com traceback no log e exibidos como mensagem genérica; nunca engolidos.

## A.12.5 Contrato da estratégia (Strategy)

```python
class PDFTextStrategy(Protocol):
    name: str                      # identificador estável (ex.: "concursos")
    display_name: str              # texto da UI
    implemented: bool              # False => aparece como "em breve" e não selecionável
    def extract(self, reader: PDFReader, pages: Sequence[int],
                config: ExtractionConfig,
                progress: ProgressCallback | None = None,
                cancel: CancellationToken | None = None) -> ExtractionResult: ...
```

Regras: a estratégia não conhece widgets, Streamlit nem CustomTkinter; recebe configuração por objeto; devolve estrutura tipada; sinaliza problemas via `warnings` e exceções do domínio; preserva número de página e ordem; processa **incrementalmente** (página a página/ em janelas) e faz uma passagem de amostragem para detectar ruído repetido (A.13.2) sem carregar o documento inteiro. O `registry.py` expõe as estratégias disponíveis; adicionar uma nova não exige alterar UI nem motor de áudio (teste que comprove isso com uma estratégia fake).

## A.12.6 Contrato do TTS (backend injetável)

```python
class TTSBackend(Protocol):
    async def list_voices(self, locale: str = "pt-BR") -> list[VoiceInfo]: ...
    async def synthesize_to_file(self, text: str, voice: str, rate: str,
                                 dest: Path, cancel: CancellationToken | None) -> None: ...
```

O `EdgeTTSBackend` implementa; testes usam `FakeTTSBackend` (gera bytes MP3 válidos mínimos ou simulados, falhas programáveis, latência simulada). **Antes de implementar**, inspecione a API real instalada do `edge-tts` (classe `Communicate`, métodos de `save`/`stream`, parâmetros `rate`/`volume`/`pitch`, função de listagem de vozes, chaves dos dicionários de voz) e registre em ADR o que foi verificado.

## A.12.7 Concorrência (decisão a ser registrada em ADR na Fase 4)

- `audio_service` expõe uma API `async` e um **facade síncrono** que executa o loop em **uma thread de trabalho própria** (um único loop por job; nunca `asyncio.run()` dentro de um contexto com loop ativo).
- Progresso e cancelamento por `ProgressCallback` + `CancellationToken` (baseado em `threading.Event`), independentes de qualquer toolkit.
- **Desktop:** o worker publica eventos em uma `queue.Queue`; a thread da UI consome com `after()`. Nunca toque em widgets fora da thread da UI.
- **Streamlit:** o job roda em thread de trabalho com objeto de estado guardado em `st.session_state` (somente referência ao job e seu estado serializável); a UI consulta o estado (polling com `st.fragment`/`st.rerun`, conforme API verificada na versão instalada). Não recrie loops a cada reexecução do script.
- Teste a lógica de concorrência com `FakeTTSBackend`, incluindo cancelamento no meio e falha no segmento N.

---

# A.13 REQUISITOS DETALHADOS POR ÁREA

## A.13.1 Seleção de páginas (RF-03)

Função pura `parse_page_selection(expr: str, total_pages: int) -> PageSelection`:
- Aceita `1`, `1, 3, 5-10, 15`, espaços extras; opcionalmente `;` como separador (documente).
- Páginas começam em 1; limite superior ≤ total; rejeita `0`, negativos, `10-5`, `5-`, `-5`, `a-b`, tokens vazios (`1,,2`), caracteres inválidos, números absurdamente grandes (verifique antes de expandir intervalo: não materialize ranges enormes; valide limites por aritmética antes).
- Remove duplicatas e ordena **crescentemente** (decisão fixa, registrada em ADR).
- Entrada vazia: **erro** `SelecaoPaginasError`. "Todas as páginas" é uma ação explícita separada (`PageSelection.all(total)`), com botão/checkbox na interface.
- Entrada inválida **nunca** vira "todas as páginas".
- Mensagens de erro apontam o token problemático. A UI mostra "N páginas serão processadas".
- Testes parametrizados: ≥ 25 casos (válidos, inválidos, fronteiras: página 1, última página, total=1, sobreposição `1-5, 3-7`, espaços, Unicode como `–` (en dash) e `‑`: decida se aceita e documente).

## A.13.2 Extração de PDF (RF-01, 02, 05–08)

**Validação:** existe; é arquivo regular; abre com PyMuPDF; sem senha (ou erro específico `PDFProtegidoError`; **não** peça nem armazene senha nesta versão); total de páginas ≥ 1; amostragem de texto: se todas as páginas selecionadas estiverem sem texto → `PDFSemTextoError` com mensagem sugerindo PDF pesquisável. Páginas isoladas sem texto → aviso, não erro. Feche sempre o documento (context manager).

**Cabeçalhos/rodapés/marcas d'água (conservador, explicável, configurável):**
1. Combine sinais: (a) faixa vertical superior/inferior configurável em % da altura; (b) repetição do mesmo texto normalizado (dígitos substituídos por `#`) em ≥ X% das páginas amostradas (X configurável, padrão sugerido: 40%, ajustável em ADR); (c) padrões de numeração (`Página 3 de 120`, `3/120`, `- 3 -`); (d) para marca d'água/licenciamento: texto rotacionado, em cor clara/baixa opacidade ou repetido diagonalmente, quando a biblioteca fornecer esses dados.
2. **Só remova** quando ≥ 2 sinais concordarem, ou 1 sinal forte (padrão de numeração isolado na margem). Nunca remova só por estar perto da margem.
3. Todo bloco removido gera registro (`NoiseRecord`: página, motivo, texto truncado em hash/trecho curto) acessível em modo debug **sem** gravar texto integral em logs.
4. Opção `remove_headers_footers=False` desativa tudo.
5. Teste negativo obrigatório: nota de rodapé legal ou artigo na margem **não** é removido.

**Estratégia Concursos (hipóteses a validar com PDFs reais, se disponíveis):** materiais desse tipo costumam ter cabeçalho/rodapé com nome do curso/professor e URL, numeração de páginas, marca de licenciamento personalizada (nome/CPF do aluno), caixas de destaque, quadros-resumo, questões comentadas com banca/ano (ex.: "(CESPE/2019)") e gabaritos. **Não presuma**: inspecione os PDFs reais, se fornecidos; caso contrário, implemente padrões **configuráveis** (lista de regex em arquivo de configuração) e documente que foram inferidos. Pontos específicos:
- Marcas de licenciamento com dados pessoais **não devem ser lidas em voz alta** (e isso também é uma boa prática de privacidade); remova-as quando identificadas com confiança e informe nos avisos.
- Banca/ano em questões: mantenha como parte do texto, formatando de modo legível ("Questão da banca CESPE, de 2019" **somente** se o formato for inequívoco).
- Alternativas "a), b)…" e gabaritos: preserve a estrutura em linhas/itens separados, com pausas claras.
- Destaques e caixas: leia na posição do fluxo, sem inserir rótulos inventados.

**Ordem de leitura (RF-06):** use blocos do PyMuPDF (`get_text("dict")` ou equivalente verificado) com coordenadas. Detecte colunas por agrupamento de x (histograma de bordas esquerdas / intervalo vazio vertical contínuo). Se detectar 2+ colunas: ordene coluna a coluna, e dentro delas por y. Blocos que abrangem largura total (títulos) separam seções de colunas. Se a confiança for baixa, volte à ordem nativa do PDF/ordem conservadora e emita aviso. Cubra com fixtures sintéticas (1 coluna, 2 colunas, título de largura total + 2 colunas, caixa lateral).

**Tabelas/figuras/fórmulas (RF-07):** opções configuráveis em `ExtractionConfig`: `tables = ignore | linear | marker`, `figures = ignore | marker`. Padrão sugerido: `tables=marker` (ex.: "[Tabela nesta página]") e `figures=ignore`, com **aviso agregado** ("3 figuras e 1 tabela não foram lidas"). Detecte tabelas com recurso do PyMuPDF (verificar disponibilidade na versão instalada; se indisponível, heurística simples ou apenas marcador). Fórmulas: preserve o texto extraído; não aplique substituição de símbolos matemáticos (`%`, `+`, `=`, `/`, `<`, `>`) fora de contextos seguros e testados.

**Digitalizados (RF-08):** página sem texto + com imagem de página inteira ⇒ aviso "possível página digitalizada". Sem OCR nesta versão. Nunca gerar áudio vazio como sucesso.

**Performance (RNF-08):** extração via gerador por página; passagem de amostragem limitada (ex.: até N páginas distribuídas, configurável); meça com um PDF sintético de 500 páginas (teste de desempenho marcado `@pytest.mark.slow`) e registre tempo/memória aproximados.

## A.13.3 Normalização para narração (RF-09, 10)

**Arquitetura:** lista ordenada de **etapas puras** (`str -> str` ou `Document -> Document`), cada uma com nome, função, testes e flag de habilitação em configuração. A ordem é documentada em `ARQUITETURA.md` e fixada em um teste que verifica a lista de etapas. Nada de uma cadeia solta de `re.sub`.

**Ordem recomendada:**
1. Limpeza de caracteres de controle, espaços, normalização Unicode (NFC), hífens e aspas especiais, remoção de caracteres de largura zero e *soft hyphen*.
2. Reconstrução de linhas/parágrafos (A.13.4).
3. Símbolos e abreviações jurídicas com contexto (`Art.`, `Arts.`, `§`, `§§`, `nº`, `n.º`, `inc.`, `al.`, `c/c`, `p. ex.`).
4. Referências legais e datas **antes** dos números genéricos (para evitar leitura incorreta de `8.666/93`).
5. Ordinais, cardinais, decimais, percentuais, moeda.
6. Siglas e expressões frequentes (dicionário configurável, com limites de palavra).
7. Ajustes de prosódia (pontuação, pausas entre itens de lista, espaços).
8. Validação final: texto não vazio, estatísticas, avisos.

**Regra de ouro:** melhorar a pronúncia, nunca alterar o conteúdo. Na dúvida, **mantenha o texto original** e registre aviso.

**Invariantes automatizados (teste de propriedade/ou testes parametrizados):**
- A normalização nunca devolve texto vazio para entrada não vazia.
- Nenhuma palavra maior é alterada por substituição parcial (teste: `Artigo`, `Particular`, `Martin`, `Parágrafo` permanecem intactos).
- Todo token numérico da entrada ou aparece intacto na saída ou foi convertido por uma regra **suportada e documentada** (teste que lista as regras).
- `normalize` é **determinística**; avalie idempotência (`normalize(normalize(x)) == normalize(x)`) e documente os casos em que não vale.

**Decisão a registrar em ADR (Fase 3):** usar biblioteca para extenso numérico (por exemplo `num2words` com locale `pt_BR`, verificar instalação e comportamento) **ou** implementação própria. Avalie: cobertura de milhares/milhões, feminino/masculino ("uma", "duas", "duzentas"), ordinais até 1000, "e" correto, cardinal de anos. Se usar biblioteca, isole em `text/numbers.py` e cubra os pontos onde o resultado precisa de ajuste. Tenha em mente que o próprio serviço de TTS já lê alguns números sozinho: **não expanda por padrão o que o TTS lê bem** (valide manualmente na Fase 4 e registre).

**Casos obrigatórios (golden tests em `tests/golden/*.tsv` ou `.yaml`: entrada, saída esperada, observação).** Mínimo de 80 casos, incluindo — **os resultados abaixo são esperados como ilustração; valide e ajuste conforme a decisão linguística registrada em ADR**:

| Entrada | Saída esperada (ilustrativa) |
|---|---|
| `Art. 5º, inciso II` | `Artigo quinto, inciso dois` (ou `inciso segundo`; decidir em ADR) |
| `Art. 37, caput` | `Artigo trinta e sete, caput` |
| `Arts. 5º e 6º` | `Artigos quinto e sexto` |
| `§ 1º` / `§ 2º` | `parágrafo primeiro` / `parágrafo segundo` |
| `§ 10` | `parágrafo dez` |
| `§ 1º do art. 7º` | `parágrafo primeiro do artigo sétimo` |
| `Lei 8.666/93` | `Lei oito mil seiscentos e sessenta e seis, de noventa e três` |
| `Lei nº 14.133, de 1º de abril de 2021` | `Lei número catorze mil cento e trinta e três, de primeiro de abril de dois mil e vinte e um` |
| `Decreto-Lei 200/67` | leitura de número e ano; hífen preservado como pausa curta |
| `10%` / `2,5%` | `dez por cento` / `dois vírgula cinco por cento` |
| `R$ 1.250,00` | `mil duzentos e cinquenta reais` |
| `01/02/2020` | preservar ambíguo? Decidir: padrão pt-BR dd/mm/aaaa ⇒ `primeiro de fevereiro de dois mil e vinte` (só com validação de dia/mês) |
| `3/4` (fração? data? artigo?) | **manter original** em caso ambíguo |
| `CESPE/2019` | manter estrutura; ano por extenso opcional |
| `Art. ` no meio de palavra, ex.: `Martin`, `Particular`, `Cart.` | **não alterar** |
| `II - ...` (inciso) | `inciso dois`/`inciso segundo` **apenas** com contexto de dispositivo; em `Capítulo II`, `Rei João II`, `Século XX` tratar separadamente |
| `a)` / `b)` | `alínea a` / `alínea b` somente em contexto de enumeração jurídica; caso contrário, manter |
| `1.234.567` | `um milhão, duzentos e trinta e quatro mil, quinhentos e sessenta e sete` |
| `1.234,56` | decimal pt-BR |
| `2020/2021` | **manter** (pode ser período, não lei) |

Inclua casos **negativos** (não deve alterar), **de fronteira** (início/fim de linha, pontuação colada) e **regressões** descobertas durante o projeto.

**Decisões linguísticas a registrar (ADR):** leitura de incisos (cardinal vs ordinal), de artigos até 9 (ordinal) e a partir de 10 (cardinal), de `§ único` ("parágrafo único"), de "caput", de números de lei com separador de milhar, de siglas (ler letra a letra ou como palavra: dicionário configurável, ex.: `STF`, `CF/88`, `CPC`, `CP`, `CLT`, `OAB`; `CF/88` ⇒ "Constituição Federal de oitenta e oito" só se confirmado como padrão).

**Prosódia:** não use SSML a menos que a versão instalada do `edge-tts` o suporte comprovadamente (verifique; versões recentes tratam o texto de forma específica). Pausas devem vir de pontuação (vírgula, ponto, quebra de parágrafo/segmento). Não converta todo ponto em pausa nem toda quebra de linha em espaço.

## A.13.4 Quebras de linha e parágrafos

- Una linhas quebradas no meio de frase (linha termina sem pontuação final e a próxima começa em minúscula, por exemplo).
- Preserve parágrafos por evidência (espaçamento vertical maior que o normal, recuo, linha anterior terminando em ponto e a próxima iniciando em maiúscula).
- Hifenização de fim de linha: una `pala-\nvra` somente se o resultado for plausível (heurística + lista de prefixos/compostos como `ex-`, `vice-`, `semi-`, `anti-`); em dúvida, preserve o hífen e registre aviso.
- Preserve itens de lista, incisos (`I -`), alíneas (`a)`) e parágrafos legais (`§`) como unidades separadas por pausa.
- Cabeçalhos de seção (títulos) terminam com pausa; evite juntá-los ao corpo.

## A.13.5 Motor de áudio (RF-11 a 14, 17)

**Vozes:** consulte dinamicamente; filtre `pt-BR`; exiba só campos que a biblioteca fornecer. Sem lista fixa. Se a consulta falhar: mensagem + "tentar novamente"; só use voz padrão se **verificada como disponível** na resposta atual do serviço; caso contrário, bloqueie com orientação.

**Segmentação (`audio/chunking.py`):**
- Executa **depois** da normalização (a normalização remove abreviações com ponto, o que evita cortes errados), mas o segmentador também deve **ignorar pontos de abreviações** residuais (`Dr.`, `Sr.`, `etc.`, `p.`, `n.º`).
- Prioridade de corte: parágrafo > frase > vírgula/ponto e vírgula > espaço (último recurso, **nunca** cortar no meio de palavra ou de número).
- Limite configurável em caracteres (valor padrão **conservador** definido após verificar a documentação/comportamento do serviço; registre em ADR a justificativa e como foi verificado; não invente limite).
- Testes: texto sem pontuação; parágrafo único gigante; frase maior que o limite; texto curto; abreviações; números com separador; preservação da ordem; soma dos segmentos equivale ao texto original (ignorando espaços normalizados).

**Geração:**
- Um segmento por requisição; arquivos intermediários em diretório temporário criado com `tempfile` (único por job), removido ao concluir, falhar ou cancelar (`try/finally`).
- **Junção de MP3:** na Fase 4, faça um **spike técnico** curto: gerar 2–3 segmentos reais (teste manual com rede, se o ambiente permitir) e avaliar (a) concatenação direta dos fluxos MP3 produzidos pelo mesmo serviço e voz, validando o resultado com leitura de cabeçalhos/frames (por exemplo `mutagen`, se adotado) e (b) alternativa com FFmpeg/pydub. Escolha a opção **mais simples que produza um arquivo válido e tocável**, registre em ADR a evidência, e documente a dependência se houver. Se o ambiente não tiver rede, registre a limitação, implemente atrás de uma interface `Mp3Joiner` e deixe o teste manual descrito em `docs/TESTE_MANUAL_TTS.md`.
- Escrita atômica: grave em `nome.mp3.part` no mesmo diretório e finalize com `os.replace`; trate permissões, disco cheio, caminho inexistente, arquivo aberto no Windows.
- Colisão de nomes: política `ask` (UI pergunta), `rename` (sufixo ` (1)`), `overwrite` (somente com confirmação explícita). Nunca sobrescreva silenciosamente.
- Validação pós-gravação: existe, tamanho > 0, cabeçalho MP3 plausível, e (se possível) duração > 0.
- Retentativas: no máximo 3 por segmento, espera progressiva (ex.: 1s, 2s, 4s com jitter), apenas para erros transitórios (rede/timeout); informe o usuário a cada retentativa; falhou ⇒ erro claro com o número do segmento; **nada de arquivo parcial apresentado como sucesso**.
- Velocidade (`rate`): aceite um valor percentual em faixa validada (ex.: −50% a +100%), formatado como a biblioteca exigir (verifique o formato real).
- Estimativa de duração: heurística por número de palavras/caracteres, **rotulada como estimativa** na UI.
- Cancelamento: o token é verificado entre segmentos e, quando possível, durante o stream; ao cancelar, limpe temporários e não deixe `.part`.

## A.13.6 Interface Desktop (RF-15)

CustomTkinter, salvo ADR. Título exato: **"Matraca - Leitor de PDFs"**. Campos: seleção do PDF; nome, total de páginas e estado; páginas (com opção "todas"); estratégia/modo (Concursos, Padrão, Legislação seca desabilitada com rótulo "em breve"); voz pt-BR; velocidade; botão de prévia (texto bruto × normalizado, em abas ou lado a lado, com contagem de caracteres/avisos); caminho de saída; iniciar; progresso e estado; cancelar; mensagens amigáveis.

Requisitos: nunca bloquear a thread de UI; desabilitar controles incompatíveis durante tarefas; validar antes de iniciar; preservar seleções; permitir nova operação após sucesso/falha/cancelamento; layout utilizável em resoluções comuns (≥ 1280×720) e DPI alto; textos em pt-BR.

**Arquitetura da GUI (para ser testável):** padrão MVP. `presenter.py` contém estado, validações e orquestração dos serviços do núcleo (**sem importar customtkinter**); `desktop_app.py` é a View mínima. Teste o presenter com view falsa (sem display). Se o ambiente for headless, teste a View apenas com `xvfb-run` quando disponível ou registre a limitação e forneça roteiro manual de teste. Linux: documente a dependência do pacote do sistema do Tk (ex.: `python3-tk`) e como verificar.

## A.13.7 Interface Web com Streamlit (RF-16)

Entrada `app_web.py` (fina) que invoca `matraca.web.streamlit_app`. Título da página: **"Matraca"**. Funcionalidade equivalente à Desktop: upload, total de páginas, páginas, modo, voz, velocidade, prévia, nome de saída, iniciar, progresso, download do MP3.

- Respeite o modelo de reexecução do Streamlit: `st.session_state` apenas para estado de UI e referência ao job; nada de variáveis globais para estado de sessão; arquivos grandes não permanecem na sessão indefinidamente (use diretório temporário por sessão e limpe ao concluir/descartar).
- Limite de upload configurável (`.streamlit/config.toml` → `server.maxUploadSize`, e checagem no código com a mesma constante de configuração; documente que é configurável e não universal).
- Sanitize **sempre** o nome do arquivo enviado (apenas o *basename*, remova separadores, `..`, caracteres de controle e reservados do Windows, limite de comprimento); o arquivo é gravado em temporário gerado, nunca com o nome enviado como caminho.
- Valide tipo por cabeçalho (`%PDF-`) e não só pela extensão.
- Alerta claro no README e na UI antes de expor publicamente: sem autenticação, uso pensado para execução local; texto vai ao serviço remoto de TTS.
- Teste a lógica da página com `streamlit.testing.v1.AppTest`, se disponível na versão instalada; caso contrário, extraia a lógica para funções testáveis em `matraca/web/`.

## A.13.8 Segurança, privacidade, logs (RNF-04, 05)

- Sem `eval`/`exec`, sem `shell=True` com entrada do usuário (se usar FFmpeg: lista de argumentos, `subprocess.run([...])`, sem shell).
- Valide caminhos de saída (diretório existente e gravável; resolva e normalize; proíba escrever sobre o próprio PDF de origem).
- Logging: nível INFO sem conteúdo do PDF; DEBUG pode incluir **contagens e hashes**, nunca texto integral; rotação de arquivo de log; local do log documentado; sem tokens nem dados pessoais.
- README com seção "Privacidade": o texto é enviado ao serviço remoto durante a síntese, exige internet e pode ser alterado ou ficar indisponível sem aviso (serviço não oficial/ não garantido: **verifique e descreva com precisão** o status do serviço consumido pela biblioteca, sem afirmações infundadas).
- Verificação de dependências: `pip-audit` se disponível (opcional), registre o resultado real.

## A.13.9 Qualidade e testes (RNF-02, 03)

- Type hints em toda API pública; docstrings e comentários em **português**; nomes claros e consistentes (identificadores em inglês **ou** português, mas escolha **um** padrão e registre em ADR).
- Sem `except Exception: pass`; sem valores padrão silenciosos que escondam erros.
- Cobertura: meça com `pytest-cov`; metas sugeridas: ≥ 90% em `page_selection`, `text/`, `audio/chunking`; ≥ 80% no `core/`. Reporte o número **real**.
- Marcadores `pytest`: `unit`, `integration`, `slow`, `manual` (os `manual` nunca rodam por padrão).
- **Fixtures sintéticas** geradas por `scripts/make_fixtures.py` (use PyMuPDF para criar PDFs; evite binários grandes versionados): (1) uma coluna com parágrafos quebrados em linhas; (2) duas colunas; (3) cabeçalho/rodapé repetidos com numeração; (4) apenas imagem (sem camada textual); (5) protegido por senha; (6) corrompido/truncado; (7) vazio; (8) com nota de rodapé jurídica na margem inferior (teste negativo de remoção); (9) 500 páginas para teste `slow`; (10) texto jurídico com `Art.`, `§`, incisos, `Lei 8.666/93`.
- **Testes de integração mínimos:** fixture → extração → normalização → segmentos; `JobService` com `FakeTTSBackend` → MP3 simulado → validação de saída; falhas de rede simuladas (retentativa e falha final); cancelamento no meio; colisão de nome; presenter da GUI e lógica da página Web chamando o **mesmo** `JobService` (teste que verifique isso por injeção/mock).
- Os testes automatizados **não** usam rede nem o TTS real. Existe um roteiro manual (`docs/TESTE_MANUAL_TTS.md`) e um comando `python -m matraca doctor --tts` que testa o serviço real quando o usuário quiser.

## A.13.10 Diagnóstico e CLI mínima (RF-18, Should)

`python -m matraca doctor`: verifica versão do Python, dependências importáveis e suas versões, existência do tkinter, FFmpeg (se necessário), diretório de logs e temporários graváveis, e, com `--tts`, consulta de vozes e síntese curta de teste. Saída em pt-BR, sem stack trace por padrão (`--verbose` para detalhes).
`python -m matraca cli --pdf X --paginas "1-3" --modo concursos --voz Y --saida Z.mp3`: fino, usa `JobService`; serve para validar o núcleo em ambiente sem interface gráfica.

## A.13.11 Compatibilidade e dependências

- Python 3.11+ (ou a versão estável compatível com todas as dependências; **verifique** e registre em ADR).
- `requirements.txt` (runtime) e `requirements-dev.txt` (pytest, pytest-cov, ruff, mypy/pyright, etc.), com versões **mínimas verificadas** (`pip install` real e `pip freeze` registrado em ADR). `pyproject.toml` coerente com eles.
- Cada dependência justificada em ADR; sem bibliotecas para tarefas triviais da biblioteca padrão.
- Linux × Windows: documente diferenças conhecidas (Tk no Linux, caminhos, `os.replace`/arquivo aberto no Windows, codificação de console, FFmpeg no PATH, DPI, política de execução do PowerShell para ativar venv).

---

# PARTE B — PLANO DE FASES COM ENTRADAS, SAÍDAS E CRITÉRIOS VERIFICÁVEIS

Cada fase inclui: **entradas** (o que precisa existir), **tarefas**, **saídas**, **critérios de aceite verificáveis** e **armadilhas conhecidas**. Todas passam pelo portão A.8.

## Fase 0 — Inspeção, planejamento e riscos
**Entradas:** nenhuma.
**Tarefas:**
1. Inspecione o diretório de trabalho: há código existente? Git? Se sim, leia estrutura, dependências e testes sem sobrescrever nada; se não, declare projeto novo e rode `git init`.
2. Verifique ambiente: SO, `python --version`, `pip --version`, acesso à rede (teste simples e inofensivo), presença de `ffmpeg`, `tkinter`, display (`$DISPLAY`/`xvfb`), e quais pacotes podem ser instalados.
3. Se o usuário forneceu PDFs reais, inspecione-os (estrutura, colunas, cabeçalhos, marca d'água) e registre achados **sem copiar conteúdo sensível** para a documentação.
4. Reúna as perguntas bloqueantes (A.5) em uma mensagem, com hipóteses padrão.
5. Crie `CLAUDE.md`, `docs/*` (modelos na Parte C), `docs/RASTREABILIDADE.md` populado com os IDs da A.11.
6. Registre ADRs iniciais (estrutura final, padrão de nomes, Python alvo, ordem dos incisos etc. como "a decidir na Fase X").
7. Liste riscos: serviço TTS não oficial, junção de MP3, ordem de leitura em colunas, ambiguidade jurídica na normalização, Streamlit × concorrência, Tk em Linux.
**Saídas:** plano refinado, arquitetura inicial, riscos, STATUS inicial.
**Aceite:** documentos criados e coerentes; nenhuma linha de código de produto ainda; ambiente descrito com saídas reais de comandos.

## Fase 1 — Fundação e contratos
**Entradas:** Fase 0 concluída.
**Tarefas:** criar `venv`, instalar dependências com versões verificadas; estrutura de pacotes; `models.py`, `exceptions.py`, `progress.py`, `config.py`; Protocols `PDFReader`, `PDFTextStrategy`, `TTSBackend`; `utils/paths.py` (sanitização de nome, colisão, temporários) e `utils/logging_config.py`; `pyproject.toml`, `ruff`, `pytest` (com marcadores), `scripts/check.sh/.ps1`; `scripts/make_fixtures.py` esqueleto.
**Saídas:** pacote importável, contratos tipados, primeiros testes (sanitização de nomes, exceções, logging sem conteúdo).
**Aceite:** `scripts/check.sh` passa; `import matraca` sem efeitos colaterais; teste prova que `core/` não importa módulos de interface/terceiros (ex.: varredura de imports via `ast`).
**Armadilhas:** contratos grandes demais; não implemente ainda extração/áudio.

## Fase 2 — Seleção de páginas e extração
**Tarefas:** `page_selection.py` (A.13.1) com ≥ 25 casos; `PyMuPDFReader`; `pdf_service`; estratégia Padrão; `estrategia_concursos` com `noise.py` e `layout.py`; todas as fixtures sintéticas (1–8, 10); relatório de avisos/estatísticas.
**Aceite:** testes de página e de extração passam; teste negativo de nota de rodapé passa; PDF sem texto/protegido/corrompido geram os erros corretos; ordem de leitura de 2 colunas correta na fixture; nenhum teste depende de rede; evidência anexada ao STATUS (contagens reais).
**Armadilhas:** remover conteúdo legítimo; ordem de colunas por y apenas; recursos de arquivo abertos; carregar o PDF todo em memória.

## Fase 3 — Pipeline de normalização
**Tarefas:** etapas puras e ordem fixada; `legal_terms`, `numbers` (ADR da biblioteca vs. própria), `dates`, `linebreaks`; golden tests (≥ 80 casos); invariantes (A.13.3); `docs/EXEMPLOS_NORMALIZACAO.md` gerado a partir dos golden; estatísticas e avisos.
**Aceite:** todos os golden e invariantes passam; casos ambíguos preservados; nenhum regex aplicado sem limites de palavra; revisão manual de 20 casos aleatórios do golden documentada.
**Armadilhas:** `Lei 8.666/93` virar data; `II` em "Rei João II"; `Art.` em palavras; leitura de ano; explosão de regras sem teste.

## Fase 4 — Motor de áudio
**Tarefas:** inspeção real da API do `edge-tts` + ADR; `TTSBackend` + `EdgeTTSBackend` + `FakeTTSBackend`; `chunking`; `audio_service` e `job_service`; progresso, cancelamento, retentativas, escrita atômica; spike de junção de MP3 (A.13.5) + ADR; `doctor --tts` e `docs/TESTE_MANUAL_TTS.md`; CLI mínima.
**Aceite:** testes com fake cobrem sucesso, falha de rede transitória (retenta e funciona), falha permanente, cancelamento, disco/permissão, colisão de nome; nenhum `.part`/temporário remanescente após qualquer desfecho (teste); se houver rede, execute o teste manual e registre o resultado **real**; se não houver, registre explicitamente que o TTS real **não foi verificado**.
**Armadilhas:** `asyncio.run` em loop ativo; concatenar MP3 sem validar; retentativa infinita; vazamento de threads.

## Fase 5 — Interface Desktop
**Tarefas:** `presenter.py` testável; `desktop_app.py` (View); fila de eventos do worker → UI; estados (ocioso, validando, extraindo, gerando, concluído, erro, cancelado); testes do presenter; verificação em tela (xvfb ou manual).
**Aceite:** testes do presenter cobrem validação, sucesso, falha, cancelamento e nova tentativa; nenhuma importação de lógica de extração/normalização/TTS na View; roteiro manual de verificação visual anexado; limitações de ambiente registradas.
**Armadilhas:** widgets alterados fora da thread da UI; UI congelada durante prévia de PDF grande (prévia também em segundo plano).

## Fase 6 — Interface Web
**Tarefas:** `streamlit_app.py` + `app_web.py`; upload seguro; prévia; geração em thread com polling; download; limpeza de temporários; `.streamlit/config.toml`; testes com `AppTest` ou funções extraídas.
**Aceite:** upload com nome malicioso (`../../x.pdf`, nome muito longo, caracteres reservados) é sanitizado (teste); arquivo > limite rejeitado (teste); app inicia (`streamlit run app_web.py` com verificação de saúde, se possível no ambiente) ou limitação registrada; mesmo `JobService` que o Desktop.
**Armadilhas:** estado perdido em reexecuções; novo loop a cada clique; arquivos temporários acumulados; exposição pública sem aviso.

## Fase 7 — Integração, regressão, revisão
**Tarefas:** suíte completa + cobertura + ruff + mypy/pyright + compileall; teste `slow` de 500 páginas; revisão de segurança/privacidade (checklist abaixo); revisão de duplicação entre UIs; limpeza de temporários em todos os desfechos; revisão da rastreabilidade: todo RF/RNF **Must** com teste e status real.
**Checklist de revisão final:**
- [ ] Nenhum texto de PDF em logs padrão.
- [ ] Nenhum `eval`/`exec`/`shell=True`.
- [ ] Nomes de arquivo sanitizados em todas as entradas.
- [ ] Nenhum temporário remanescente após sucesso/erro/cancelamento.
- [ ] Desktop e Web chamam `JobService`.
- [ ] Mensagens de erro em pt-BR, sem stack trace na UI.
- [ ] Limitações (digitalizados, tabelas, figuras, conectividade) visíveis no README **e** na UI.
**Aceite:** relatório de validação honesto, com números reais, pendências e riscos.

## Fase 8 — Documentação e entrega
**Tarefas:** README final (instalação e execução em Linux e Windows, Streamlit, Desktop, testes, diagnóstico, privacidade, limitações, solução de problemas comuns); `ARQUITETURA.md` com diagrama do fluxo; `EXEMPLOS_NORMALIZACAO.md`; revisão de todos os documentos; árvore final.
**Aceite:** um leitor consegue, seguindo **apenas** o README, instalar e executar do zero (simule em um `venv` limpo e registre o resultado); o STATUS reflete o estado real.

---

# PARTE C — MODELOS DE ARQUIVOS PARA O AGENTE CRIAR

## C.1 `CLAUDE.md` (≤ 120 linhas; atualizar a cada fase)

```markdown
# Matraca — guia operacional para o agente
Objetivo: PDF → MP3 (pt-BR) para estudo de concursos. Núcleo único; UIs finas.

## Comandos
- Instalar: <preencher>
- Checagem completa: scripts/check.sh | scripts/check.ps1
- Testes: pytest -q  | lentos: pytest -m slow | manuais: pytest -m manual
- Desktop: python app_desktop.py   Web: streamlit run app_web.py
- Diagnóstico: python -m matraca doctor [--tts]

## Regras que não podem ser esquecidas
1. Fidelidade > pronúncia: na dúvida, manter o texto original.
2. Nenhuma lógica de negócio nas UIs; tudo via core/job_service.py.
3. core/ não importa gui/web/edge_tts/fitz (usa Protocols).
4. Testes não usam rede; TTS real só em testes manuais.
5. Nunca declarar sucesso sem executar; registrar saída real.
6. Sem texto de PDF em logs. Sem eval/shell=True.
7. Escrita atômica de MP3 (.part → os.replace); limpar temporários sempre.
8. Verificar APIs de terceiros na instalação real antes de usar.

## Estado
Ver docs/STATUS_DO_PROJETO.md → "Retomada rápida".

## Mapa de módulos
<tabela curta: pasta → responsabilidade>

## Decisões vigentes (ADRs)
<lista de 1 linha por ADR>
```

## C.2 `docs/STATUS_DO_PROJETO.md`

```markdown
# Status do projeto
## Retomada rápida (máx. 25 linhas)
- Fase atual: 
- Último commit/tag: 
- Funciona (verificado por teste): 
- Quebrado/pendente: 
- Decisões pendentes (com hipótese padrão): 
- PRÓXIMO PASSO EXATO: 
- Comandos para validar: 

## Histórico por fase
### Fase N — título (data)
- Concluído: 
- Evidência (comando → resultado real): 
- Riscos/limitações: 
```

## C.3 `docs/DECISOES_TECNICAS.md` (modelo de ADR)

```markdown
## ADR-NNN — Título
- Data / Fase:
- Contexto:
- Decisão:
- Alternativas consideradas:
- Evidência verificada (comando/saída ou documentação consultada):
- Consequências / riscos:
- Status: proposta | aceita | substituída por ADR-XXX
```

## C.4 `docs/RASTREABILIDADE.md`

```markdown
| ID | Descrição | Prioridade | Módulo(s) | Teste(s) | Status (não iniciado/parcial/concluído) | Evidência |
|----|-----------|-----------|-----------|----------|------|-----------|
| RF-03 | Seleção de páginas | Must | core/page_selection.py | tests/unit/test_page_selection.py | | |
```

## C.5 Prompt curto de retomada (para o humano colar em sessões novas)

```text
Retome o projeto Matraca. Siga o protocolo de retomada (seção A.3 do prompt/CLAUDE.md):
leia CLAUDE.md, STATUS (Retomada rápida) e RASTREABILIDADE; rode git status, git log e
scripts/check.sh; confirme o estado real e execute o PRÓXIMO PASSO EXATO. Pare ao final da fase.
```

---

# PARTE D — ENTREGA FINAL (Fase 8)

Apresente:
- árvore final de diretórios;
- resumo das funcionalidades **realmente implementadas** (referenciando IDs RF/RNF e status real);
- comandos de instalação/execução para **Linux** e **Windows** (Desktop e Web);
- comandos de testes, cobertura e diagnóstico;
- organização e justificativa das dependências (versões verificadas);
- limitações conhecidas (PDFs digitalizados, tabelas, figuras, fórmulas, conectividade/serviço TTS, ordem de leitura em layouts complexos);
- decisões adiadas para versões futuras (OCR, `LivroStrategy`, `LeiSecaStrategy`, empacotamento, dicionário de pronúncia do usuário, retomada de geração);
- resultados **reais** de todos os testes e verificações executados, incluindo o que **não** pôde ser verificado e por quê.

Não declare concluído o que está apenas planejado. Não esconda limitações. Se algum requisito não foi atendido, diga qual e o que falta.

---

# INSTRUÇÃO INICIAL

Execute a **Fase 0** agora. Primeiro examine o ambiente e os arquivos existentes (A.3 e Fase 0). Depois apresente o plano objetivo, as perguntas bloqueantes com hipóteses padrão (A.5) e os riscos, crie os documentos de controle e atualize `docs/STATUS_DO_PROJETO.md`. **Não gere classes nem interfaces do produto ainda.** Pare ao final da fase e aguarde "prossiga", a menos que eu tenha pedido execução contínua.
