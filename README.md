# 🎙️ Transcripty

Transcripty é uma aplicação web em **Python + Streamlit** para:

-   Gravar reuniões em tempo real pelo navegador
-   Transcrever automaticamente o áudio utilizando IA
-   Gerar **resumos estruturados** com os principais pontos e acordos
-   Armazenar histórico de reuniões para consulta posterior

O objetivo do projeto é transformar reuniões faladas em **documentação
clara, organizada e reutilizável**.

------------------------------------------------------------------------

## 🚀 Funcionalidades

-   🎤 Gravação de áudio em tempo real via WebRTC
-   🧠 Transcrição automática com modelo de speech‑to‑text
-   📝 Geração automática de resumo da reunião
-   📂 Organização por data e título
-   🔎 Visualização de reuniões anteriores
-   ⏱️ Temporizador de gravação em tempo real

------------------------------------------------------------------------

## 🏗️ Arquitetura

Fluxo principal:

1.  Usuário inicia gravação no navegador
2.  Áudio é capturado e salvo localmente
3.  Trechos são enviados para transcrição automática
4.  Texto completo é armazenado
5.  Um resumo estruturado é gerado via LLM
6.  Reuniões ficam disponíveis para consulta futura

------------------------------------------------------------------------

## 📦 Estrutura do Projeto

    Transcripty/
    │
    ├── main.py              # Aplicação principal Streamlit
    ├── requirements.txt     # Dependências do projeto
    ├── audios/              # Reuniões gravadas e transcrições
    └── README.md

------------------------------------------------------------------------

## ⚙️ Instalação

``` bash
git clone https://github.com/LorenzoMarty/Transcripty.git
cd Transcripty
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🔑 Variáveis de Ambiente

Crie um arquivo `.env`:

    OPENAI_API_KEY=sua_chave_aqui

------------------------------------------------------------------------

## ▶️ Executando o Projeto

``` bash
streamlit run main.py
```

Abra no navegador:

    http://localhost:8501

------------------------------------------------------------------------

## 🧠 Tecnologias Utilizadas

-   Python
-   Streamlit
-   WebRTC
-   Pydub
-   Speech‑to‑Text (Whisper ou similar)
-   LLMs para resumo automático

------------------------------------------------------------------------

## 👤 Autor

**Lorenzo Marty**\
GitHub: https://github.com/LorenzoMarty
