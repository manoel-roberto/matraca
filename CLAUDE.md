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
Ver docs/STATUS_DO_PROJETO.md → "Retomada rápida".

## Mapa de módulos
| Pasta | Responsabilidade |
|---|---|
| `matraca/core/` | modelos, exceções, progresso, `ports.py` (Protocols), serviços (stdlib apenas) |
| `matraca/config.py` | dataclasses de configuração imutáveis |
| `matraca/utils/` | `paths` (sanitização, colisão, temporários), `logging_config` |
| `matraca/pdf/` | adaptador PyMuPDF (único que importa fitz) |
| `matraca/extractors/` | estratégias de extração |
| `matraca/text/` | etapas puras de normalização |
| `matraca/audio/` | chunking, edge-tts (adaptador), MP3 |
| `matraca/gui/`, `matraca/web/` | interfaces finas |
| `tests/` | unit, integration, golden, fixtures (sintéticas via scripts/make_fixtures.py) |

## Decisões vigentes (ADRs)
- ADR-001 estrutura A.12.2 · ADR-002 Python 3.12 (min 3.11) · ADR-003 identificadores em inglês, docs pt-BR
- ADR-004 dependências verificadas · ADR-005 mypy (proposta)
