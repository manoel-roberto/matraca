# Rastreabilidade

Status: `não iniciado` / `parcial` / `concluído`. Atualizado ao fim de cada fase.

| ID | Descrição | Prioridade | Módulo(s) | Teste(s) | Status | Evidência |
|----|-----------|-----------|-----------|----------|--------|-----------|
| RF-01 | Validar PDF | Must | pdf/pymupdf_reader.py, core/pdf_service.py | tests/unit/test_pdf_service.py | não iniciado | |
| RF-02 | Total de páginas; processar só as selecionadas, em ordem | Must | core/pdf_service.py, extractors/ | tests/unit/test_extractors.py | não iniciado | |
| RF-03 | Seleção de páginas por expressão | Must | core/page_selection.py | tests/unit/test_page_selection.py | não iniciado | |
| RF-04 | Estratégias intercambiáveis | Must | extractors/registry.py, base.py | tests/unit/test_registry.py | não iniciado | |
| RF-05 | Remoção conservadora de cabeçalho/rodapé/marca d'água | Must | extractors/noise.py | tests/unit/test_noise.py | não iniciado | |
| RF-06 | Ordem de leitura (colunas) | Must | extractors/layout.py | tests/unit/test_layout.py | não iniciado | |
| RF-07 | Tabelas, figuras, fórmulas configuráveis | Must | extractors/ | tests/unit/test_extractors.py | não iniciado | |
| RF-08 | Detecção de páginas sem texto | Must | pdf/, extractors/ | tests/unit/test_extractors.py | não iniciado | |
| RF-09 | Pipeline de normalização pt-BR | Must | text/ | tests/golden, tests/unit/test_normalization*.py | não iniciado | |
| RF-10 | Prévia bruto × normalizado + estatísticas | Should | core/job_service.py, gui/, web/ | tests/integration | não iniciado | |
| RF-11 | Vozes pt-BR dinâmicas | Must | audio/edge_tts_client.py | tests/unit/test_voices.py | não iniciado | |
| RF-12 | Segmentação segura | Must | audio/chunking.py | tests/unit/test_chunking.py | não iniciado | |
| RF-13 | Geração assíncrona com progresso/cancelamento | Must | core/audio_service.py, job_service.py | tests/integration/test_job_service.py | não iniciado | |
| RF-14 | Escrita segura do MP3 | Must | audio/mp3_writer.py | tests/unit/test_mp3_writer.py | não iniciado | |
| RF-15 | Interface Desktop | Must | gui/ | tests/unit/test_presenter.py | não iniciado | |
| RF-16 | Interface Web | Must | web/, app_web.py | tests/unit/test_web_logic.py | não iniciado | |
| RF-17 | Velocidade da voz | Should | audio/, config.py | tests/unit/test_rate.py | não iniciado | |
| RF-18 | `doctor` e CLI mínima | Should | cli.py, doctor.py | tests/unit/test_doctor.py | não iniciado | |
| RNF-01 | Núcleo único; sem lógica nas UIs | Must | todo o projeto | tests/unit/test_architecture.py | não iniciado | |
| RNF-02 | Testes sem rede nem TTS real | Must | tests/ | suíte completa | não iniciado | |
| RNF-03 | Type hints, docstrings pt-BR | Must | todo o projeto | mypy, ruff | não iniciado | |
| RNF-04 | Segurança (sem eval, sem traversal, sem texto em logs) | Must | utils/, logging_config | tests/unit/test_security.py | não iniciado | |
| RNF-05 | Aviso de privacidade (TTS remoto) | Must | README, UIs | revisão manual | não iniciado | |
| RNF-06 | Linux e Windows | Should | scripts/, README | check.ps1 (não executável aqui) | não iniciado | |
| RNF-07 | UI nunca congela | Must | gui/presenter, web/ | tests/unit/test_presenter.py | não iniciado | |
| RNF-08 | Memória controlada (incremental) | Must | extractors/ | tests/integration/test_perf_500p.py (slow) | não iniciado | |
