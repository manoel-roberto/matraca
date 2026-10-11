# Roteiro de Teste Manual da Interface Desktop (CustomTkinter)

Este roteiro descreve a verificação visual e interativa da interface Desktop do Matraca (RF-15, A.13.6).

## Execução
```bash
python app_desktop.py
```
*(No Linux, certifique-se de que o pacote `python3-tk` do sistema esteja instalado e que a variável `DISPLAY` esteja ativa, ex.: `DISPLAY=:0`).*

---

## Passos de Verificação Visual e Funcional

1. **Abertura da Janela:**
   - O título deve ser exatamente: **"Matraca - Leitor de PDFs"**.
   - Tamanho inicial mínimo: 900x700 px, com elementos redimensionáveis e barra de rolagem se a tela for menor.
   - Tema moderno ativado (CustomTkinter).

2. **Seleção de Arquivo PDF:**
   - Clique em "Procurar..." e selecione um PDF de teste (ex: `tests/fixtures/texto_juridico.pdf`).
   - O rótulo deve exibir: "Total: N página(s) | Camada de texto: Sim".
   - O campo "Salvar MP3 em:" deve ser preenchido automaticamente com o mesmo nome do PDF e extensão `.mp3`.
   - A opção "Todas as páginas" deve vir marcada por padrão com o intervalo `1-N` preenchido.

3. **Configuração de Parâmetros:**
   - Desmarque "Todas as páginas" e digite um subconjunto (ex: `1, 2`).
   - Selecione a voz desejada no combobox dinâmico pt-BR (ex: `pt-BR-AntonioNeural`).
   - Ajuste o slider de velocidade de -50% a +100% e confira se o rótulo ao lado reflete o percentual (ex: `+20%`).
   - Escolha o modo de extração (Concursos ou Padrão).

4. **Prévia do Texto:**
   - Clique em **"Ver Prévia do Texto"**.
   - A janela modal de prévia deve abrir com 3 abas:
     - **Texto Normalizado:** com números por extenso, artigos e leis formatados para fala.
     - **Texto Original Bruto:** sem formatação para comparação 1:1.
     - **Estatísticas e Avisos:** contagem de parágrafos, caracteres, palavras e eventuais alertas.

5. **Início da Conversão e Progresso:**
   - Clique em **"Iniciar Conversão"**.
   - Os botões "Iniciar" e "Procurar..." devem ficar desabilitados, e o botão "Cancelar" habilitado.
   - A barra de progresso e o rótulo de status devem atualizar em tempo real refletindo as etapas:
     `Iniciando síntese...` -> `Sintetizando segmento 1 de N...` -> `Gravando arquivo final...`
   - Ao concluir, uma caixa de diálogo deve exibir a mensagem de sucesso com tamanho e duração aproximada.

6. **Cancelamento:**
   - Inicie a conversão de um arquivo grande e clique imediatamente em **"Cancelar"**.
   - A operação deve ser abortada imediatamente e nenhum arquivo corrompido `.part` deve permanecer no disco.
