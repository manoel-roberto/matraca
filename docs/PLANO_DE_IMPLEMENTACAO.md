# Plano de implementação

Fonte: `Prompt_Matraca_v2.md` (Parte B). Toda fase passa pelo portão A.8 (`scripts/check.sh`).

| Fase | Título | Critério de aceite (resumo) |
|------|--------|-----------------------------|
| 0 | Inspeção, planejamento, riscos | Docs de controle criados; ambiente descrito com saídas reais; nenhum código de produto |
| 1 | Fundação e contratos | `check.sh` passa; `import matraca` sem efeitos; teste AST prova que `core/` não importa terceiros/UI |
| 2 | Seleção de páginas e extração | ≥ 25 casos de páginas; teste negativo de rodapé jurídico; erros corretos (sem texto/protegido/corrompido); 2 colunas na ordem certa |
| 3 | Normalização | ≥ 80 golden; invariantes; casos ambíguos preservados; revisão manual de 20 casos |
| 4 | Motor de áudio | Testes com fake (sucesso, retentativa, falha, cancelamento, disco, colisão); sem `.part`/temporários; spike MP3; TTS real verificado ou declarado não verificado |
| 5 | Desktop | Presenter testado sem display; View sem lógica de negócio; roteiro manual |
| 6 | Web | Upload sanitizado e limitado; mesmo `JobService`; app inicia ou limitação registrada |
| 7 | Integração e revisão | Suíte + cobertura + ruff + mypy; teste `slow` 500 páginas; checklist de segurança |
| 8 | Documentação e entrega | README reproduzível em venv limpo; STATUS fiel |

## Escopo fora desta versão (A.9)
OCR, banco de dados, contêineres, serviços pagos, descrição de imagens, empacotamento, detecção automática de tipo de documento, `LeiSecaStrategy`/`LivroStrategy` funcionais.

## Riscos
| Risco | Mitigação |
|-------|-----------|
| Serviço TTS não oficial pode mudar/ficar indisponível | `TTSBackend` injetável; `doctor --tts`; ADR com o que foi verificado |
| Junção de MP3 | Spike na Fase 4; interface `Mp3Joiner`; validação por `mutagen` |
| Ordem de leitura em colunas | Detecção por histograma + fallback conservador + aviso |
| Ambiguidade jurídica na normalização | Regra de ouro: na dúvida, manter original; golden tests |
| Streamlit × concorrência | Thread de trabalho + estado em `session_state` (só referência) |
| Tk em Linux | Documentar `python3-tk`; presenter testado sem display |
| Remover conteúdo legítimo como ruído | ≥ 2 sinais; teste negativo obrigatório |
