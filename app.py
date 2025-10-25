import streamlit as st
import requests
from audio_recorder_streamlit import audio_recorder
import base64
from gtts import gTTS
import io

st.set_page_config(page_title="Amalia - Mon Assistant IA 🤖", page_icon="🤖")

st.title("🤖 Amalia - Ton assistant IA vocal")
st.write("Écris ou parle, Amalia te répondra à l'oral !")

# Initialiser l'historique
if "history" not in st.session_state:
    st.session_state.history = []

# Fonction pour transcrire l'audio avec Groq
def transcribe_audio(audio_bytes):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    files = {
        "file": ("audio.wav", audio_bytes, "audio/wav"),
        "model": (None, "whisper-large-v3"),
        "language": (None, "fr")
    }
    
    try:
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json().get("text", "")
    except:
        pass
    return None

# Fonction pour obtenir la réponse d'Amalia
def get_amalia_response(user_input):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et créative. Réponds de manière concise."}]
    
    for msg in st.session_state.history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["assistant"]})
    
    messages.append({"role": "user", "content": user_input})
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except:
        pass
    return "Désolée, une erreur s'est produite."

# Fonction pour convertir texte en audio
def text_to_speech(text):
    tts = gTTS(text=text, lang='fr', slow=False)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes.getvalue()

# Fonction pour auto-play audio
def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Interface principale
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input("Pose ta question ici:", key="text_input")

with col2:
    st.write("")  # Espacement
    audio_bytes = audio_recorder(
        text="🎤",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_size="2x"
    )

# Traiter l'audio si enregistré
if audio_bytes:
    with st.spinner("🎧 Écoute en cours..."):
        transcription = transcribe_audio(audio_bytes)
        if transcription:
            user_input = transcription
            st.success(f"Tu as dit : {transcription}")

# Bouton d'envoi
if st.button("Envoyer") and user_input:
    with st.spinner("Amalia réfléchit..."):
        answer = get_amalia_response(user_input)
        
        # Sauvegarder dans l'historique
        st.session_state.history.append({"user": user_input, "assistant": answer})
        
        # Générer et jouer l'audio
        audio_response = text_to_speech(answer)
        autoplay_audio(audio_response)

# Afficher l'historique
st.markdown("---")
st.markdown("### 💬 Historique des conversations")

for msg in st.session_state.history:
    with st.chat_message("user"):
        st.write(msg["user"])
    with st.chat_message("assistant"):
        st.write(msg["assistant"])
        # Bouton pour réécouter
        audio_replay = text_to_speech(msg["assistant"])
        st.audio(audio_replay, format="audio/mp3")




