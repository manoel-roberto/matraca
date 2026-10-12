# 🎧 Matraca — Leitor de PDFs para Concursos Públicos

Transforma apostilas e livros em formato PDF em audiolivros MP3 com narração fluente em português do Brasil, especialmente calibrado para o estudo de concursos públicos.

O Matraca remove cabeçalhos, rodapés e ruídos de página repetitivos (com suporte especializado a materiais do **Estratégia Concursos**), normaliza termos jurídicos, leis e números para pronúncia natural e gera arquivos MP3 através de vozes neurais de alta fidelidade sem custo de API.

---

## 🚀 Funcionalidades Principais

- **Extração Inteligente de Layout:** Detecção de colunas, remoção de cabeçalhos de aula, rodapés com marcas de professor e numerações repetitivas.
- **Pipeline de Normalização Jurídica em 9 Etapas:**
  - Leis e Decretos: `"Lei 8.666/93"` → *"Lei oito mil seiscentos e sessenta e seis de noventa e três"*.
  - Artigos: `"Art. 5º"` → *"Artigo quinto"*; `"Art. 10"` → *"Artigo dez"*.
  - Parágrafos: `"§ 1º"` → *"Parágrafo primeiro"*; `"§ único"` → *"Parágrafo único"*.
  - Incisos: `"inciso IV"` → *"inciso quatro"*.
  - Datas, Horários, Moedas e Siglas expandidos de forma compreensível.
- **Vozes Neurais pt-BR:** Vozes naturais de alta qualidade (`pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaNeural`) com controle de velocidade (-50% a +100%).
- **Interfaces Modernas e Coesas:**
  - **Interface Web (Streamlit):** Upload seguro com validação de tamanho e tipo, prévia do texto, barra de progresso em tempo real e download direto do MP3.
  - **Interface Desktop (CustomTkinter):** Aplicação para desktop com tema escuro elegante, janela modal de prévia com abas e cancelamento imediato.
  - **Linha de Comando (CLI):** Processamento rápido em lote e diagnóstico de ambiente (`doctor`).
- **Escrita Atômica de Áudio:** Gravação com sufixo temporário (`.part`) e renomeação atômica (`os.replace`), garantindo arquivos íntegros validados por metadados ID3/MPEG.

---

## 📦 Download dos Executáveis Prontos (Windows & Linux)

Se você deseja apenas utilizar o Matraca sem precisar instalar Python ou configurar ambiente de desenvolvimento, baixe os executáveis pré-compilados diretamente da nossa página de lançamentos:

👉 **[Acessar Última Versão (GitHub Releases)](https://github.com/manoel-roberto/matraca/releases/latest)**

| Sistema Operacional | Arquivo | Como Executar |
| :--- | :--- | :--- |
| **Linux (x86_64)** | `matraca-desktop` | [Instruções para Linux](#-como-executar-a-versão-desktop-no-linux) |
| **Windows 10/11 (x86_64)** | `matraca-desktop.exe` | [Instruções para Windows](#-como-executar-a-versão-desktop-no-windows) |

---

### 🐧 Como Executar a Versão Desktop no Linux

No Linux, executáveis baixados da internet não possuem permissão de execução ativada por padrão. Siga os passos abaixo:

#### 1. Conceder Permissão de Execução

**Via Terminal (Recomendado):**
Abra o terminal na pasta onde baixou o arquivo (geralmente `Downloads`) e execute:
```bash
chmod +x matraca-desktop
```

**Via Interface Gráfica:**
1. Abra o gerenciador de arquivos (Nautilus, Dolphin, Thunar, etc.).
2. Clique com o botão direito no arquivo `matraca-desktop` e selecione **Propriedades**.
3. Na aba **Permissões**, marque a opção **"Permitir execução do arquivo como programa"** (ou *"Allow executing file as program"*).

#### 2. Executar a Aplicação

- **Pelo Terminal:**
  ```bash
  ./matraca-desktop
  ```
- **Pelo Gerenciador de Arquivos:**
  Dê dois cliques sobre o arquivo `matraca-desktop`.

> [!NOTE]
> O executável já contém o interpretador Python, o CustomTkinter e todas as dependências empacotadas. Você precisa apenas de um ambiente de desktop gráfico comum (GNOME, KDE, XFCE, etc., sob X11 ou Wayland/XWayland).

---

### 🪟 Como Executar a Versão Desktop no Windows

#### 1. Executar o Arquivo
Basta dar dois cliques no executável baixado: `matraca-desktop.exe`.

#### 2. Aviso do Windows SmartScreen (Primeira Execução)
Por se tratar de um binário novo gerado via compilação automatizada (GitHub Actions) sem certificado corporativo pago, o Windows Defender SmartScreen pode exibir um aviso protetor:

1. Na janela azul de aviso, clique no link **"Mais informações"** (*"More info"*).
2. Em seguida, clique no botão **"Executar assim mesmo"** (*"Run anyway"*).

---

## 📋 Executando a Partir do Código-Fonte (Desenvolvedores)

Se preferir rodar o projeto diretamente com o Python e código-fonte:

- **Python:** 3.11 ou 3.12 instalado.
- **Conexão com a Internet:** Necessária durante a etapa de síntese de voz para consulta às vozes neurais.
- **Sistema Operacional:** Linux ou Windows 10/11.

### 1. Clonar o repositório
```bash
git clone https://github.com/manoel-roberto/matraca.git
cd matraca
```

### 2. Criar e ativar o ambiente virtual

**No Linux / macOS (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
> *Nota para Linux:* Se você pretende utilizar a interface Desktop e receber erro de Tkinter, instale o pacote do sistema:
> ```bash
> sudo apt install python3-tk  # Debian/Ubuntu
> sudo dnf install python3-tkinter  # Fedora
> ```

**No Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> *Dica PowerShell:* Se o PowerShell bloquear a execução de scripts, execute como Administrador ou no usuário atual:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Instalar as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Para instalar também as ferramentas de desenvolvimento, linters e testes:
```bash
pip install -r requirements-dev.txt
```

---

## 💻 Como Usar

### 🌐 1. Interface Web (Streamlit)
Recomendada para quem busca praticidade no navegador:
```bash
streamlit run app_web.py
```
Acesse `http://localhost:8501` no seu navegador. Você poderá enviar um PDF (limite de 50 MB), inspecionar as páginas, visualizar a prévia do texto normalizado e baixar o MP3 gerado.

### 🖥️ 2. Interface Desktop (CustomTkinter)
Aplicação desktop nativa com janela fluida, tema escuro e prévia interativa:

- **Com o executável baixado da Release:**
  - **Linux:** execute `./matraca-desktop` (consulte os [detalhes de permissões](#-como-executar-a-versão-desktop-no-linux)).
  - **Windows:** dê dois cliques em `matraca-desktop.exe`.
- **A partir do código-fonte:**
  ```bash
  python app_desktop.py
  ```

### ⌨️ 3. Linha de Comando (CLI) e Diagnóstico

**Diagnóstico do ambiente (`doctor`):**
```bash
python -m matraca doctor
```
Para testar a conectividade real com os servidores de síntese de áudio:
```bash
python -m matraca doctor --tts
```

**Processar um PDF diretamente via CLI:**
```bash
python -m matraca run caminho/para/aula.pdf --pages "1-5" --mode concursos --voice "pt-BR-FranciscaNeural" --speed 10 --output aula_01.mp3
```

**Ver apenas a prévia do texto no terminal (sem gerar MP3):**
```bash
python -m matraca run caminho/para/aula.pdf --pages "1-3" --preview
```

---

## 🧪 Testes e Portão de Qualidade

O Matraca adota verificação contínua rigorosa de qualidade com 100% de testes automatizados executando localmente sem depender de rede externa:

**Executar todas as verificações do portão de qualidade (ruff, mypy strict, compileall, testes):**
- **Linux:**
  ```bash
  ./scripts/check.sh
  ```
- **Windows:**
  ```powershell
  .\scripts\check.ps1
  ```

**Executar suíte rápida de testes:**
```bash
pytest
```

**Executar teste de regressão de documentos extensos (500 páginas):**
```bash
pytest -m slow
```

**Medir cobertura de testes:**
```bash
pytest --cov=matraca --cov-report=term-missing
```

---

## 🛡️ Privacidade e Segurança

1. **Processamento Local:** Toda a abertura do PDF, extração de texto, detecção de colunas, remoção de ruídos e normalização gramatical ocorrem **estritamente de forma local** na sua máquina. Nenhum dado do PDF é gravado em servidores externos nem transmitido para telemetria.
2. **Síntese de Áudio Remota (TTS):** Durante a fase de síntese, os segmentos de texto normalizados são enviados através de conexão criptografada (HTTPS/WSS) para os servidores do serviço Microsoft Edge TTS para geração do fluxo de áudio.
3. **Dados Sigilosos:** Se o seu documento contiver segredos industriais, dados pessoais sensíveis ou informações protegidas por sigilo judicial/legal que você não deseje transmitir para a API de síntese, **não utilize a síntese de áudio**.
4. **Interface Web Local:** A aplicação Web Streamlit não conta com sistema de autenticação ou controle de acesso multiusuário; foi concebida exclusivamente para execução local (`localhost`).

---

## ⚠️ Limitações Conhecidas

- **PDFs Digitalizados / Escaneados:** O Matraca exige que o PDF contenha uma camada de texto digitalizável. Se o PDF for composto puramente por fotos/scans sem OCR prévio, o sistema emitirá um aviso e interromperá a extração da página vazia.
- **Tabelas Complexas:** Estruturas tabulares com dezenas de células mescladas são sinalizadas com marcadores descritivos para preservar a fluidez do estudo auditivo.
- **Gráficos e Figuras:** Elementos visuais não textuais são ignorados ou marcados sinteticamente para não gerar ruídos na leitura.
- **Conectividade:** A conversão final para áudio MP3 depende de acesso à internet estável.

---

## 🔧 Solução de Problemas Comuns

- **`ModuleNotFoundError: No module named '_tkinter'`:**
  O interpretador Python do seu sistema operacional não inclui os bindings do Tk. No Ubuntu/Debian, resolva com: `sudo apt install python3-tk`.
- **`ExecutionPolicy` no PowerShell do Windows:**
  Caso o comando `.venv\Scripts\Activate.ps1` falhe com erro de permissão, abra o PowerShell e execute:
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
- **Porta em uso no Streamlit:**
  Se a porta padrão `8501` estiver ocupada, execute definindo uma porta alternativa:
  `streamlit run app_web.py --server.port 8502`.
- **Áudio cortado ou erro de síntese:**
  Execute `python -m matraca doctor --tts` para diagnosticar latência e integridade da sua conexão com o serviço de TTS.

---

## 📄 Licença
Distribuído sob a licença MIT. Consulte o arquivo de licença para mais informações.
