# Rastreabilidade

Status: `não iniciado` / `parcial` / `concluído`. Atualizado ao fim de cada fase.

| ID | Descrição | Prioridade | Módulo(s) | Teste(s) | Status | Evidência |
|----|-----------|-----------|-----------|----------|--------|-----------|
| RF-01 | Validar PDF | Must | pdf/pymupdf_reader.py, core/pdf_service.py | tests/unit/test_extraction.py | concluído | test_extraction.py: protegido/corrompido/vazio/inexistente/pasta (fase 2) |
| RF-02 | Total de páginas; processar só as selecionadas, em ordem | Must | core/pdf_service.py, extractors/ | tests/unit/test_extraction.py | concluído | test_extraction.py: seleção, ordem e progresso |
| RF-03 | Seleção de páginas por expressão | Must | core/page_selection.py | tests/unit/test_page_selection.py | concluído | test_page_selection.py: 49 casos (19 válidos + 25 inválidos + 5) |
| RF-04 | Estratégias intercambiáveis | Must | extractors/registry.py, base.py | tests/unit/test_registry.py | concluído | test_registry.py: 5 testes (estratégia fake sem tocar UI/áudio) |
| RF-05 | Remoção conservadora de cabeçalho/rodapé/marca d'água | Must | extractors/noise.py | tests/unit/test_noise_layout.py | concluído | test_extraction.py + test_noise_layout.py: negativo de rodapé jurídico OK |
| RF-06 | Ordem de leitura (colunas) | Must | extractors/layout.py | tests/unit/test_noise_layout.py | concluído | fixtures 1 col, 2 col, título+2 col, caixa lateral; layout unitário |
| RF-07 | Tabelas, figuras, fórmulas configuráveis | Must | extractors/ | tests/unit/test_extraction.py | concluído | test_noise_layout.py: marker/ignore/linear e figuras (fórmulas preservadas) |
| RF-08 | Detecção de páginas sem texto | Must | pdf/, extractors/ | tests/unit/test_extraction.py | concluído | somente_imagem e pagina_em_branco -> PDFSemTextoError; aviso por página |
| RF-09 | Pipeline de normalização pt-BR | Must | text/, core/text_pipeline.py | tests/unit/test_normalization_golden.py, test_normalization_invariants.py | concluído | 88 testes golden (100%), 5 invariantes, revisão manual de 20 casos |
| RF-10 | Prévia bruto × normalizado + estatísticas | Should | core/text_pipeline.py, job_service.py, gui/, web/ | tests/unit/test_text_pipeline.py, tests/integration | concluído | TextPipelineService gera NarrationText com alinhamento 1:1; JobService.get_preview |
| RF-11 | Vozes pt-BR dinâmicas | Must | audio/edge_tts_client.py | tests/unit/test_audio_service.py | concluído | edge-tts 7.2.8 verificado, filtro pt-BR dinâmico, FakeTTSBackend e manual |
| RF-12 | Segmentação segura | Must | audio/chunking.py | tests/unit/test_chunking.py | concluído | Parágrafos > frases > vírgulas > palavras; preserva abreviações e números |
| RF-13 | Geração assíncrona com progresso/cancelamento | Must | core/audio_service.py, job_service.py | tests/integration/test_job_service.py | concluído | AudioService com retentativa transitória, cancelamento limpo e thread dedicada |
| RF-14 | Escrita segura do MP3 | Must | audio/mp3_writer.py | tests/unit/test_mp3_writer.py | concluído | Escrita atômica .part -> os.replace, validação mutagen, limpeza de resíduos |
| RF-15 | Interface Desktop | Must | gui/ | tests/unit/test_presenter.py | concluído | CustomTkinter, MVP com DesktopPresenter testável sem display, thread-safe |
| RF-16 | Interface Web | Must | web/, app_web.py | tests/unit/test_web_logic.py | concluído | Streamlit, upload seguro, 50MB, temporário por sessão, prévia e AppTest |
| RF-17 | Velocidade da voz | Should | audio/, config.py | tests/unit/test_audio_service.py | concluído | format_rate(-50% a +100%) validado e repassado ao serviço TTS |
| RF-18 | `doctor` e CLI mínima | Should | cli.py, doctor.py | tests/unit/test_doctor.py, test_cli.py | concluído | python -m matraca doctor [--tts] e subcomando run com --preview |
| RNF-01 | Núcleo único; sem lógica nas UIs | Must | todo o projeto | tests/unit/test_architecture.py | concluído | JobService centraliza PDF + texto + áudio; Desktop e Web usam JobService |
| RNF-02 | Testes sem rede nem TTS real | Must | tests/ | suíte completa | concluído | Todos os testes usam FakeTTSBackend e fixtures locais; sem rede por padrão |
| RNF-03 | Type hints, docstrings pt-BR | Must | todo o projeto | mypy, ruff | concluído | mypy strict OK (44 arquivos), ruff OK |
| RNF-04 | Segurança (sem eval, sem traversal, sem texto em logs) | Must | utils/, logging_config | tests/unit/test_security.py, test_paths.py | concluído | Sem eval/exec/shell=True, sanitização rigorosa de arquivos |
| RNF-05 | Aviso de privacidade (TTS remoto) | Must | README, UIs | revisão manual | concluído | Aviso claro nas UIs Desktop e Web sobre TTS remoto |
| RNF-06 | Linux e Windows | Should | scripts/, README | check.ps1 (não executável aqui) | não iniciado | |
| RNF-07 | UI nunca congela | Must | gui/presenter, web/ | tests/unit/test_presenter.py | não iniciado | |
| RNF-08 | Memória controlada (incremental) | Must | extractors/ | tests/integration/test_perf_500p.py (slow) | não iniciado | |
