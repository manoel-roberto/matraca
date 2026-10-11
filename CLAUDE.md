# Matraca — guia operacional para o agente
Objetivo: PDF → MP3 (pt-BR) para estudo de concursos. Núcleo único; UIs finas.
Fonte da verdade do escopo: `Prompt_Matraca_v2.md`.

## Comandos
- Instalar: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt`
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
9. Respostas ao usuário em português do Brasil.

## Estado
Todas as Fases (0 a 8) concluídas. Ver docs/STATUS_DO_PROJETO.md.

## Mapa de módulos
| Pasta | Responsabilidade |
|---|---|
| `matraca/core/` | Modelos, exceções, progresso, `ports.py`, serviços centrais (`job_service`, `pdf_service`, `audio_service`, `text_pipeline`) |
| `matraca/config.py` | Dataclasses de configuração imutáveis |
| `matraca/utils/` | `paths` (sanitização, colisão, temporários), `logging_config` |
| `matraca/pdf/` | Adaptador PyMuPDF (`pymupdf_reader.py`) |
| `matraca/extractors/` | Extração por layout, detecção de colunas, remoção de ruídos e Estratégia Concursos |
| `matraca/text/` | Pipeline de 9 etapas de normalização pt-BR (leis, artigos, incisos, números, datas, prosódia) |
| `matraca/audio/` | Segmentação inteligente (`chunking.py`), cliente `edge_tts`, backend fake para testes e junção atômica de MP3 |
| `matraca/gui/` | Interface Desktop com CustomTkinter e padrão MVP (`presenter.py` testável sem display) |
| `matraca/web/` | Interface Web com Streamlit (`page_logic.py` e `streamlit_app.py`) |
| `matraca/doctor.py` | Diagnóstico de integridade do ambiente e conectividade TTS |
| `matraca/cli.py` | Interface de linha de comando para automação |
| `tests/` | Testes unitários, de integração, golden tests e testes de desempenho (500 páginas) |

## Decisões vigentes (ADRs)
- ADR-001 a ADR-005: Fundação, padrões de nomenclatura, versões e ferramentas de lint/tipo.
- ADR-006 a ADR-008: PyMuPDF como leitor PDF, extração de texto estruturado com BBox.
- ADR-009 e ADR-010: Detecção heurística de ruídos (cabeçalho/rodapé repetidos) e colunas.
- ADR-011 e ADR-012: Pipeline de normalização em 9 etapas e ordenação estrita.
- ADR-013 a ADR-015: edge-tts como backend de áudio, junção de MP3 e loop assíncrono em thread isolada.
- ADR-016: Padrão MVP desacoplado para Desktop e comunicação thread-safe via fila.
- ADR-017: Arquitetura Streamlit com sanitização rígida de upload, temporários por sessão e JobService central.
