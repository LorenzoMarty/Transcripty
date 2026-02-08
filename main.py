from pathlib import Path
from datetime import datetime
import time
import queue

import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import pydub
import openai
from dotenv import load_dotenv

load_dotenv()

PASTA_AUDIO = Path(__file__).parent / "audios"
PASTA_AUDIO.mkdir(exist_ok=True)

chat = openai.OpenAI()


def chat_openai(mensagem, modelo="gpt-4o-mini"):
    mensagens = [{"role": "user", "content": mensagem}]
    resposta = chat.chat.completions.create(model=modelo, messages=mensagens)
    return resposta.choices[0].message.content


# =========================
# Utilitários Arquivo
# =========================
def salva_arquivo(caminho_arquivo: Path, conteudo: str):
    caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)


def ler_arquivo(caminho_arquivo: Path) -> str:
    if caminho_arquivo.exists():
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def salvar_titulo(pasta_reuniao: Path, titulo: str):
    salva_arquivo(pasta_reuniao / "titulo.txt", titulo)


# =========================
# Grava / Transcreve audio
# =========================
def transcreve_audio(caminho_audio: Path, language="pt", response_format="text"):
    with open(caminho_audio, "rb") as arquivo_audio:
        transcricao = chat.audio.transcriptions.create(
            model="whisper-1",
            language=language,
            response_format=response_format,
            file=arquivo_audio,
        )
    return transcricao  # para response_format="text", isso costuma ser uma string


def adiciona_chunk_audio(frames_de_audio, audio_segment: pydub.AudioSegment):
    for frame in frames_de_audio:
        sound = pydub.AudioSegment(
            data=frame.to_ndarray().tobytes(),
            sample_width=frame.format.bytes,
            frame_rate=frame.sample_rate,
            channels=len(frame.layout.channels),
        )
        audio_segment += sound
    return audio_segment


def gravar_audio():
    webrtx_ctx = webrtc_streamer(
        key="recebe_audio",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        media_stream_constraints={"video": False, "audio": True},
    )

    if not webrtx_ctx.state.playing:
        return

    container = st.empty()
    container.markdown("Comece a falar")
    temporarizador = st.empty()

    pasta_reuniao = PASTA_AUDIO / datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    pasta_reuniao.mkdir(exist_ok=True)

    caminho_audio_completo = pasta_reuniao / "audio.mp3"
    caminho_audio_temp = pasta_reuniao / "audio_temp.mp3"
    caminho_transcricao = pasta_reuniao / "transcricao.txt"

    ultima_transcricao = time.time()
    inicio_gravacao = time.time()
    audio_chunk = pydub.AudioSegment.empty()
    audio_completo = pydub.AudioSegment.empty()
    transcricao_total = ""

    while webrtx_ctx.state.playing:
        agora = time.time()
        tempo_decorrido = int(agora - inicio_gravacao)

        minutos = tempo_decorrido // 60
        segundos = tempo_decorrido % 60

        temporarizador.markdown(f"⏱️ **Tempo de gravação:** {minutos:02d}:{segundos:02d}")

        try:
            frames_de_audio = webrtx_ctx.audio_receiver.get_frames(timeout=1)
        except queue.Empty:
            time.sleep(0.05)
            continue

        audio_completo = adiciona_chunk_audio(frames_de_audio, audio_completo)
        audio_chunk = adiciona_chunk_audio(frames_de_audio, audio_chunk)

        if len(audio_chunk) > 0:
            audio_completo.export(caminho_audio_completo, format="mp3")

            if agora - ultima_transcricao > 15:
                ultima_transcricao = agora

                audio_chunk.export(caminho_audio_temp, format="mp3")
                transcricao_chunk = transcreve_audio(caminho_audio_temp)

                transcricao_total += str(transcricao_chunk)
                salva_arquivo(caminho_transcricao, transcricao_total)

                container.markdown(transcricao_total)
                audio_chunk = pydub.AudioSegment.empty()


# =========================
# Utilitários reunião
# =========================
def listar_reunioes():
    lista_reunioes = sorted(PASTA_AUDIO.glob("*"), reverse=True)
    reunioes = {}

    for reuniao in lista_reunioes:
        if not reuniao.is_dir():
            continue

        data_reuniao = reuniao.stem
        try:
            ano, mes, dia, hora, minuto, segundo = data_reuniao.split("_")
            label = f"{ano}/{mes}/{dia} {hora}:{minuto}:{segundo}"
        except ValueError:
            label = data_reuniao

        titulo = ler_arquivo(reuniao / "titulo.txt")
        if titulo.strip():
            label += f" - {titulo.strip()}"

        reunioes[data_reuniao] = label

    return reunioes


def gerar_resumo(pasta_reuniao: Path):
    transcricao = ler_arquivo(pasta_reuniao / "transcricao.txt")
    if not transcricao.strip():
        salva_arquivo(pasta_reuniao / "resumo.txt", "Sem transcrição ainda.")
        return

    prompt = f"""
Faça o resumo do texto delimitado por ###.
O texto é a transcrição de uma reunião.
O resumo deve contar com os principais assuntos abordados.
O resumo deve ter no máximo 300 caracteres.
O resumo deve estar em texto corrido.
No final, deve ser apresentados todos acordos feitos na reunião no formato de bullet points.
Abaixo dos acordo feitos deve haver quem propos o acordo.

Formato:
Resumo reunião:
- ...

Acordos da Reunião:
- acordo 1;
  - autor.
- acordo 2;
  - autor.

texto: ###{transcricao}###
"""
    resumo = chat_openai(mensagem=prompt)
    salva_arquivo(pasta_reuniao / "resumo.txt", resumo)


def selecionar_reuniao():
    reunioes = listar_reunioes()
    if not reunioes:
        st.info("Nenhuma reunião salva ainda.")
        return

    reuniao_selecionada = st.selectbox("Selecione uma reunião", list(reunioes.values()))
    st.divider()

    reuniao_data = [k for k, v in reunioes.items() if v == reuniao_selecionada][0]
    pasta_reuniao = PASTA_AUDIO / reuniao_data

    titulo_path = pasta_reuniao / "titulo.txt"
    transcricao_path = pasta_reuniao / "transcricao.txt"
    resumo_path = pasta_reuniao / "resumo.txt"

    if not titulo_path.exists():
        st.warning("Adicione um título")
        titulo_reuniao = st.text_input("Título da reunião")

        # on_click estava errado: você estava EXECUTANDO na hora.
        st.button(
            "Salvar",
            on_click=lambda: salvar_titulo(pasta_reuniao, titulo_reuniao),
            disabled=not bool(titulo_reuniao.strip()),
        )
        return

    titulo = ler_arquivo(titulo_path)
    transcricao = ler_arquivo(transcricao_path)
    resumo = ler_arquivo(resumo_path)

    if not resumo.strip():
        gerar_resumo(pasta_reuniao)
        resumo = ler_arquivo(resumo_path)

    st.markdown(f"## {titulo}")
    st.markdown(resumo)
    st.markdown("### Transcrição")
    st.write(transcricao if transcricao.strip() else "Sem transcrição ainda.")


# =========================
# Pages
# =========================
def main_pages():
    tab_gravar, tab_selecao = st.tabs(["Gravar Reunião", "Ver transcrições salvas"])

    with tab_gravar:
        gravar_audio()

    with tab_selecao:
        selecionar_reuniao()


if __name__ == "__main__":
    st.header("Bem vindo ao Transcipty🎙️", divider=True)
    main_pages()
