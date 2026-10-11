# Status do projeto

## Retomada rápida (máx. 25 linhas)
- Fase atual: 0 concluída (inspeção/planejamento). Próxima: Fase 1.
- Último commit/tag: `fase-0-concluida`
- Funciona (verificado por teste): nada de produto ainda (Fase 0 não tem código).
- Quebrado/pendente: tudo de produto.
- Decisões pendentes (com hipótese padrão): ver `docs/DECISOES_TECNICAS.md` (fim).
- PRÓXIMO PASSO EXATO: Fase 1 — estrutura de pacotes, `models.py`, `exceptions.py`, `progress.py`, `config.py`, Protocols, `utils/`, `pyproject.toml`, `scripts/check.sh`.
- Comandos para validar: `source .venv/bin/activate && scripts/check.sh` (a partir da Fase 1).

## Histórico por fase
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
