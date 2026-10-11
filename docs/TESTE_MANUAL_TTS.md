# Roteiro e Evidência do Teste Manual de TTS

Este documento registra o procedimento e o resultado do teste manual de síntese de fala com o serviço remoto `edge-tts 7.2.8` (RNF-02, RF-11 a RF-14, A.13.5).

## Ambiente do Teste
- **Data da execução:** 2026-10-11
- **Sistema Operacional:** Linux Ubuntu 22.04 (kernel 6.8.0-138-generic x86_64)
- **Python:** 3.12.13 (`.venv`)
- **Versão do edge-tts:** 7.2.8
- **Versão do mutagen:** 1.48.1

## Procedimento de Execução

1. **Diagnóstico do serviço:**
   ```bash
   python -m matraca doctor --tts
   ```
   **Resultado obtido:**
   - 3 vozes pt-BR ativas encontradas:
     - `pt-BR-AntonioNeural` (Male)
     - `pt-BR-FranciscaNeural` (Female)
     - `pt-BR-ThalitaMultilingualNeural` (Female)
   - Latência medida: ~1012 ms.
   - Status: Aprovado.

2. **Spike de síntese e junção atômica de múltiplos segmentos:**
   - Gerados 2 segmentos consecutivos de texto com `pt-BR-AntonioNeural`.
   - Concatenação binária direta de streams MP3 (mesma voz e taxa).
   - Validação com `mutagen.mp3.MP3`:
     - Duração: 5.496 segundos.
     - Bitrate: 48000 bps.
     - Canais: 1 (mono).
     - Erros de frame: 0.

3. **Verificação de Áudio Tocável:**
   - Arquivo de áudio gerado reproduzível com decodificador padrão e biblioteca mutagen.
